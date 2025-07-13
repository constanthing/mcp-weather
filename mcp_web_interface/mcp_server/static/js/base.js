let promptForm = null;
let promptInput = null;
let chatsSection = null;

document.addEventListener("DOMContentLoaded", () => {
    const csrfToken = document.querySelector("input[name='csrfmiddlewaretoken']").value;

    promptForm = document.querySelector("#chat-input");
    promptInput = document.querySelector("#prompt-input");
    chatsSection = document.querySelector("#chats");

    function deleteChat(target) {
        // e.target is the delete button 

        console.log(target)

        const chatId = target.parentElement.parentElement.dataset.chatId;

        console.log(chatId)

        // make request to server to delete chat
        fetch(`/chat/${chatId}/`, {
            method: "DELETE", 
            headers: {
                "X-CSRFToken": csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = "/";
            } else {
                console.log(data.error)
            }
        })
    }

    function permanentlyDeleteChat(target) {
        const btnParent = target.parentElement.parentElement;
        const chatId = btnParent.dataset.chatId;

        fetch(`/permanently-delete/${chatId}`, {
            method: "DELETE",
            headers: {
                "X-CSRFToken": csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // remove deleted chat item
                btnParent.remove();
            } else {
                console.log(data.error)
            }
        })
    }

    // document.querySelectorAll(".chat-history-item").forEach(item => {
    //     item.addEventListener("click", e => {
    //         // if clicked directly on the chat history item
    //         if (e.target.classList.contains("chat-history-item")) {
    //             if (e.target.classList.contains("active-chat")) {
    //                 return;
    //             }
    //             window.location.href = `/chats/${e.target.dataset.chatId}`; 
    //         }
    //         // if clicked on the p element in chat history item
    //         else if (e.target.parentElement.classList.contains("chat-history-item")) {
    //             if (e.target.parentElement.classList.contains("active-chat")) {
    //                 return;
    //             }
    //             window.location.href = `/chats/${e.target.parentElement.dataset.chatId}`; 
    //         } else if (e.target.parentElement.classList.contains("chat-history-item-delete-button")) {
    //             deleteChat(e.target.parentElement);
    //         }
    //     })
    // })

    document.querySelectorAll(".chat-history-delete-btn").forEach(btn => {
        btn.addEventListener("click", e => {
            deleteChat(e.target);
        })
    })



    document.querySelectorAll(".deleted-chat-delete-button").forEach(btn => {
        btn.addEventListener("click", e => {
            // console.log(e.target)
            permanentlyDeleteChat(e.target.parentElement);
        })
    })


    // new chat button
    document.querySelector("#new-chat-btn").addEventListener("click", () => {
        window.location.href = "/chat/";
        return;
        fetch("/unique_chat_id", {
            method: "GET",
        })
        .then(response => response.json())  
        .then(data => {
            if (data.chat_id) {
                window.location.href = `/chats/${data.chat_id}`;
            } else {
                alert("Failed to get unique chat id")
            }
        })
    })
})