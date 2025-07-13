function createUserPrompt(prompt) {
    const chatPair = document.createElement("div");
    chatPair.classList.add("chat-pair");

    const userPrompt = document.createElement("div");
    userPrompt.classList.add("user-message");
    userPrompt.innerHTML = `<p>${prompt}</p>`;

    chatPair.appendChild(userPrompt);
    chatsSection.appendChild(chatPair);

    chatsSection.scrollTo({
        top: chatsSection.scrollHeight,
        behavior: "smooth"
    })


    return chatPair;
}

function createAgentReply(reply, chatPair, model_response_time) {
    const agentReply = document.createElement("div");
    agentReply.classList.add("model-message");
    agentReply.innerHTML = reply;
    const responseFooter = document.createElement("div");
    responseFooter.classList.add("model-footer");

    const responseOptions = document.createElement("div");
    responseOptions.classList.add("model-options");

    const copyResponseButton = document.createElement("button");
    copyResponseButton.innerHTML = "<i class='bi bi-copy'></i>";
    responseOptions.appendChild(copyResponseButton);

    const downloadResponseButton = document.createElement("button");
    downloadResponseButton.innerHTML = "<i class='bi bi-download'></i>";
    responseOptions.appendChild(downloadResponseButton);

    responseFooter.appendChild(responseOptions);

    if (model_response_time) {
        const modelResponseTime = document.createElement("small");
        modelResponseTime.classList.add("model-response-time")
        modelResponseTime.textContent = `Model response time: ${model_response_time} seconds`;
        responseFooter.appendChild(modelResponseTime)
    }
    chatPair.appendChild(agentReply);
    chatPair.appendChild(responseFooter);



    // Use requestAnimationFrame to ensure the scroll happens after the DOM update
    requestAnimationFrame(() => {
        chatsSection.scrollTo({
            top: chatsSection.scrollHeight,
            behavior: "smooth"
        });
    });

    return agentReply;
}

let chatController = null;

let chatPairId = 0;

document.addEventListener("DOMContentLoaded", () => {
    const csrfToken = document.querySelector("input[name='csrfmiddlewaretoken']").value;

    const chatSendBtn = document.querySelector("#chat-send-btn");
    const chatStopBtn = document.querySelector("#chat-stop-btn");

    // model name
    const modelNameSpan = document.querySelector("#model-name");
    const modelIdentifier = modelNameSpan.dataset.modelName;

    console.log(modelIdentifier)

    let CHAT_ID = document.querySelector("#chat_id").dataset.chatId;
    console.log(CHAT_ID);

    // immediately focus on prompt input
    promptInput.focus()

    console.log(chatsSection.scrollHeight)

    promptForm.addEventListener("submit", async e => {
        e.preventDefault();

        chatSendBtn.classList.add("hidden");
        chatSendBtn.disabled = true;
        chatStopBtn.classList.remove("hidden");
        chatStopBtn.disabled = false;

        if (!CHAT_ID) {
            // create chat 
            console.log("Creating chat...")
            await new Promise((resolve, reject) => {
                fetch("/chat/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        model_name: modelIdentifier 
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        CHAT_ID = data.chat_id;
                        history.pushState(null, "", `/chat/${CHAT_ID}/`);
                    }
                })
                .finally(() => {   
                    if (!CHAT_ID) {
                        reject()
                    } else {
                        resolve();
                    }
                })
            })
            .catch(() => {
                console.log("failed to create chat (chat id creation failed)")
                return;
            })
        }

        // final check
        if (!CHAT_ID) {
            return;
        }

        // if prompt is not empty
        if (promptInput.value.length > 0) {
            // add user prompt to chat section
            const chatPair = createUserPrompt(promptInput.value);

            const thinkingContainer = document.createElement("div");
            thinkingContainer.classList.add("thinking-container");
            thinkingContainer.classList.add("active");
            thinkingContainer.id = `${chatPairId}-thinking-container`;
            thinkingContainer.innerHTML = `
                <div class="thinking-header">
                    <div>
                        <i class="bi bi-gear thinking-icon"></i>
                        <h3>Thinking Logs</h3>
                    </div>

                    <button class="thinking-expand-btn">
                        <i class="bi bi-caret-down"></i>
                        <i class="bi bi-caret-up"></i>
                    </button>
                </div>
                <div class="thinking-logs">
                </div>
            </div>
            `;
            chatPair.appendChild(thinkingContainer);

            chatPairId++;

            // promptStatusBtn.classList.add("prompt-response-loading")

            chatController = new AbortController();
            const signal = chatController.signal;

            // make request to server with prompt
            const response = await fetch(`/chat/${CHAT_ID}/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({
                    message: promptInput.value,
                }),
                signal: signal
            });

            if (!response.body) {
                console.log("Error: No response body")
                return;
            }

            if (response.status !== 200) {
                const data = await response.json();
                console.log(data.error)
                return;
            }

            let officialResponse = null;
            let v = null;

            try {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                let completeValue = "";

                while (true) {
                    let { value, done } = await reader.read();

                    if (done) {
                        break;
                    }

                    v = value;

                    // browser/network may stack buffer data, which means in one reader.read()
                    // you can get
                    // - a single chunk from one yield
                    // - multipel chunks concatentated together from several yields
                    // - partial chunk
                    value = decoder.decode(value, {stream: true});

                    completeValue += value;

                    if (!completeValue.endsWith("[DELIMITER]")) {
                        continue;
                    }

                    console.log("\n\n--------")
                    console.log(completeValue)

                    let chunks = completeValue.split("[DELIMITER]");
                    completeValue = "";

                    for (v of chunks) {
                        try {
                            console.log("====CHUNK=====")
                            console.log(v)
                            const chunk = JSON.parse(v);
                            if (chunk.status && (chunk.status == "done" || chunk.status == "error")) {
                                officialResponse = chunk;
                                break;
                            }
                            const tempDiv = document.createElement("div");

                            if (chunk.text) {
                                tempDiv.innerHTML = chunk.text;
                            } else if (chunk.status == "tool") {
                                // add tool response to chat section
                                tempDiv.innerHTML = "Tool Response";
                                tempDiv.innerHTML = `
                                    <details class=tool-response>
                                        <summary>Tool Response</summary>
                                        <div>
                                            ${JSON.stringify(chunk.data, null, 2)}
                                        </div>
                                    </details>
                                `;
                            }
                            thinkingContainer.querySelector(".thinking-logs").appendChild(tempDiv);

                            // scroll to bottom of chat section
                            requestAnimationFrame(() => {
                                chatsSection.scrollTo({
                                    top: chatsSection.scrollHeight,
                                    behavior: "smooth"
                                })
                            })
                        } catch (e) {
                            console.log("error parsing json")
                            console.log(e)
                        }
                    }
                }
            } catch (e) {
                officialResponse = {
                    status: "error",
                }
                if (e.name === "AbortError") {
                    officialResponse.error = "Stream aborted by user"
                } else {
                    officialResponse.error = e.message
                }
            } finally {
                if (officialResponse.status == "error") {
                    // add error message to chat section
                    createAgentReply(officialResponse.error, chatPair, null)
                } else {
                    // add ai agent reply to chat section
                    createAgentReply(officialResponse.data.reply, chatPair, officialResponse.data.model_response_time)
                }

                // update chat id
                // CHAT_ID = officialResponse.chat_id;

                // clear prompt input
                promptInput.value = "";
                chatSendBtn.disabled = true;

                promptInput.style.height = "auto";
                promptInput.style.height = promptInput.scrollHeight + "px";

                promptInput.focus();

                chatStopBtn.classList.add("hidden");
                chatStopBtn.disabled = true;
                chatSendBtn.classList.remove("hidden");
                chatSendBtn.disabled = true;


                thinkingContainer.classList.remove("active");
            }
        } else {
            // @TODO: Prevent form from being submittable when prompt is empty
            alert("EMPTY PROMPT")
        }
    });


    // resize prompt input
    promptInput.addEventListener("input", () => {
        promptInput.style.height = "auto";
        promptInput.style.height = promptInput.scrollHeight + "px";

        if (promptInput.value.length > 0) {
            chatSendBtn.disabled = false;
        } else {
            chatSendBtn.disabled = true;
        }
    })


    // custom prompts
    document.querySelectorAll(".custom-prompt").forEach(btn => {
        btn.addEventListener("click", () => {
            // get custom prompt details 
            fetch(`/custom_prompts/${btn.dataset.promptId}/`, {
                method: "GET",
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.log(data.error)
                        return;
                    }

                    promptInput.value = data.prompt.prompt;
                    promptInput.style.height = "auto";
                    promptInput.style.height = promptInput.scrollHeight + "px";

                    chatSendBtn.disabled = false;
                })
        })
    })

    document.addEventListener("click", e => {
        if (e.target.classList.contains("copy-response-button")) {
            console.log("copy response button clicked")
            const response = e.target.closest(".model-prompt").querySelector(".prompt-content").textContent;
            navigator.clipboard.writeText(response);
            alert("Response copied to clipboard");
        } else if (e.target.classList.contains("download-response-button")) {
            console.log("download response button clicked")
            const response = e.target.closest(".model-prompt").querySelector(".prompt-content").textContent;
            const blob = new Blob([response], { type: "text/plain" });
            const url = URL.createObjectURL(blob);
            
            // Create a temporary link element
            const downloadLink = document.createElement('a');
            downloadLink.href = url;
            downloadLink.download = 'response.txt'; // Set the filename
            downloadLink.style.display = 'none';
            
            // Append to document, click it, and remove it
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            
            // Clean up the URL object
            URL.revokeObjectURL(url);
        } else if (e.target.classList.contains("thinking-expand-btn")) {
            e.target.parentElement.parentElement.classList.toggle("expanded")
        }
    })

    document.querySelector("#chat-expand-btn").addEventListener("click", () => {    
        document.querySelector("#container").classList.toggle("expanded")
        document.querySelector("#chat-expand-btn").classList.toggle("expanded")
    })

    setTimeout(() => {
        requestAnimationFrame(() => {
            chatsSection.scrollTo({
                top: chatsSection.scrollHeight,
                behavior: "smooth"
            })
        })
    }, 300)


    document.querySelector("#chat-stop-btn").addEventListener("click", () => {
        chatController.abort();
    })


    document.querySelector("#chats").addEventListener("scroll", (e) => {
        if (e.target.scrollTop > 20) {
            document.querySelector("#chat-header").classList.add("active")
        } else {
            document.querySelector("#chat-header").classList.remove("active")
        }
    })

});