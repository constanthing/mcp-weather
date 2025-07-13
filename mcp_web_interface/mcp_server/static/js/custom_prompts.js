document.addEventListener("DOMContentLoaded", () => {
    const csrfToken = document.querySelector("input[name='csrfmiddlewaretoken']").value;

    const promptForm          = document.querySelector("#promptForm");
    const promptInput         = document.querySelector("#promptInput");
    const promptName          = document.querySelector("#promptName");
    const promptFormAddBtn = document.querySelector("#promptFormAddBtn");
    const promptFormEditBtn = document.querySelector("#promptFormEditBtn");
    const promptFormClearBtn = document.querySelector("#promptFormClearBtn");

    function deleteCustomPrompt(deleteButton) {
        deleteButton.disabled = true;

        // btn -> td -> tr (parent element)
        fetch(`/custom_prompts/${deleteButton.parentElement.parentElement.dataset.promptId}/`, {
            method: "DELETE",
            headers: {
                "X-CSRFToken": csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                deleteButton.parentElement.parentElement.remove();
            } else {
                console.log(data.error)
            }

            deleteButton.disabled = false;
        })
    }

    let selectedEditButton = null;
    function editCustomPrompt() {
        if (selectedEditButton == null) {
            alert("Selected edit button is null...")
            return;
        }

        // btn -> td -> tr (parent element)
        const editButton = selectedEditButton;
        editButton.disabled = true;
        const parentRow = editButton.parentElement.parentElement;

        fetch(`/custom_prompts/${parentRow.dataset.promptId}/`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            }, 
            body: JSON.stringify({
                prompt: promptInput.value,
                name: promptName.value
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                parentRow.querySelector(".custom-prompt-name").innerHTML = data.prompt.name;
                parentRow.querySelector(".custom-prompt-prompt").innerHTML = data.prompt.prompt;
                document.querySelector(`#prompt-${data.prompt.id}`).innerHTML = data.prompt.prompt;
            } else {
                console.log(data.error)
            }
        })
        .finally(() => {
            editButton.disabled = false;
            promptName.disabled = false;
            promptInput.disabled = false;
        })
    }

    function addCustomPrompt() {
        return new Promise((resolve, reject) => {
            fetch("/custom_prompts/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({
                    prompt: promptInput.value,
                    name: promptName.value
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addPrompt(data.prompt)
                } else {
                    console.log(data.error)
                }
            })
            .finally(() => {
                promptInput.disabled = false;
                promptName.disabled = false;
                resolve()
            })
        }) 
    }

    function addPrompt(promptData) {
        document.querySelector("tbody").innerHTML += `<div class="custom-prompt-prompt-hidden" id="prompt-${promptData.id}">${promptData.prompt}</div>`;

        const tableRow = document.createElement("tr");
        tableRow.dataset.promptId = promptData.id;

        tableRow.innerHTML = `
            <td class="custom-prompt-name">${promptData.name}</td>
            <td class="custom-prompt-prompt">${promptData.prompt}</td>
            <td>
                <button class="custom-prompt-delete-btn">
                    <i class="bi bi-trash"></i>
                </button>
                <button class="custom-prompt-edit-btn">
                    <i class="bi bi-pencil"></i>
                </button>
            </td>
        `
        document.querySelector("#custom-prompts tbody").appendChild(tableRow);
    }

    promptFormAddBtn.addEventListener("click", async e => {
        e.preventDefault();
        promptInput.disabled = true;
        promptName.disabled = true;

        await addCustomPrompt();

        promptInput.value = "";
        promptName.value = "";

        promptInput.style.height = "auto";
        promptInput.style.height = promptInput.scrollHeight + "px";

        promptFormEditBtn.disabled = true;
        promptFormClearBtn.disabled = true;
        promptFormAddBtn.disabled = true;
    })

    promptFormEditBtn.addEventListener("click", e => {
        e.preventDefault();
        promptInput.disabled = true;
        promptName.disabled = true;

        editCustomPrompt();

        promptInput.value = "";
        promptName.value = "";

        promptInput.style.height = "auto";
        promptInput.style.height = promptInput.scrollHeight + "px";

        promptFormEditBtn.disabled = true;
        promptFormClearBtn.disabled = true;
        promptFormAddBtn.disabled = true;
    })

    promptFormClearBtn.addEventListener("click", e => {
        e.preventDefault();
        promptInput.value = "";
        promptName.value = "";
        promptInput.style.height = "auto";
        promptInput.style.height = promptInput.scrollHeight + "px";

        promptFormClearBtn.disabled = true;
        promptFormAddBtn.disabled = true;
        promptFormEditBtn.disabled = true;
    })

    document.querySelector("#custom-prompts tbody").addEventListener("click", e => {
        console.log(e.target)
        if (e.target.classList.contains("custom-prompt-delete-btn")) {
            deleteCustomPrompt(e.target);
        } else if (e.target.classList.contains("custom-prompt-edit-btn")) {
            promptFormEditBtn.disabled = false;

            promptName.value = e.target.parentElement.parentElement.querySelector(".custom-prompt-name").innerText;
            promptInput.value = document.querySelector(`#prompt-${e.target.parentElement.parentElement.dataset.promptId}`).innerText;

            promptInput.style.height = "auto";
            promptInput.style.height = promptInput.scrollHeight + "px";

            selectedEditButton = e.target;
            checkPromptFormValidity();
            e.target.parentElement.classList.toggle("active");
        } else if (e.target.parentElement.tagName === "TR") {
            e.target.parentElement.classList.toggle("active");
        }
    })

    function checkPromptFormValidity() {
        if (promptName.value.length > 0 && promptInput.value.length > 0) {
            promptFormAddBtn.disabled = false;
        } else {
            promptFormAddBtn.disabled = true;
        }

        if (promptName.value.length > 0 || promptInput.value.length > 0) {
            promptFormClearBtn.disabled = false;
        } else {
            promptFormClearBtn.disabled = true;
        }
    }

    promptName.addEventListener("input", () => {
        checkPromptFormValidity();
    })

    promptInput.addEventListener("input", () => {
        checkPromptFormValidity();
        promptInput.style.height = "auto";
        promptInput.style.height = promptInput.scrollHeight + "px";
    })
})