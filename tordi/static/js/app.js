(function () {
  "use strict";

  const T = window.TORDI;
  const chatWindow = document.getElementById("chatWindow");
  const chatForm = document.getElementById("chatForm");
  const messageInput = document.getElementById("messageInput");
  const imageInput = document.getElementById("imageInput");
  const attachmentPreview = document.getElementById("attachmentPreview");
  const micBtn = document.getElementById("micBtn");
  const sendBtn = document.getElementById("sendBtn");
  const sidebar = document.getElementById("sidebar");

  let pendingImageFile = null;
  let conversationId = chatWindow ? chatWindow.dataset.conversationId : "";

  /* ---------------- helpers ---------------- */

  function scrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  function autoResize() {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 160) + "px";
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function buildMessageEl(role, content, opts) {
    opts = opts || {};
    const wrap = document.createElement("div");
    wrap.className = "message " + role;
    if (opts.id) wrap.dataset.id = opts.id;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? (window.TORDI_USERNAME || "U")[0].toUpperCase() : "T";

    const body = document.createElement("div");
    body.className = "message-body";

    if (opts.imageUrl) {
      const img = document.createElement("img");
      img.src = opts.imageUrl;
      img.className = "message-image";
      body.appendChild(img);
    }

    const textDiv = document.createElement("div");
    textDiv.className = "message-text";
    textDiv.dataset.raw = content;
    textDiv.innerHTML = escapeHtml(content).replace(/\n/g, "<br>");
    body.appendChild(textDiv);

    const actions = document.createElement("div");
    actions.className = "message-actions";
    const copyBtn = document.createElement("button");
    copyBtn.className = "msg-action copy-btn";
    copyBtn.textContent = "📋 Copy";
    actions.appendChild(copyBtn);
    if (role === "user") {
      const editBtn = document.createElement("button");
      editBtn.className = "msg-action edit-btn";
      editBtn.textContent = "✏️ Edit";
      actions.appendChild(editBtn);
    }
    body.appendChild(actions);

    wrap.appendChild(avatar);
    wrap.appendChild(body);
    return wrap;
  }

  function addTypingIndicator() {
    const wrap = document.createElement("div");
    wrap.className = "message assistant typing-indicator";
    wrap.id = "typingIndicator";
    wrap.innerHTML =
      '<div class="message-avatar">T</div>' +
      '<div class="message-body"><div class="message-text">' +
      '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>' +
      "</div></div>";
    chatWindow.appendChild(wrap);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const el = document.getElementById("typingIndicator");
    if (el) el.remove();
  }

  function clearWelcome() {
    const welcome = chatWindow.querySelector(".welcome");
    if (welcome) welcome.remove();
  }

  /* ---------------- new chat ---------------- */

  if (!conversationId) {
    chatForm && chatForm.addEventListener("submit", function (e) {
      e.preventDefault();
      // No active conversation yet: create one first via the sidebar button.
      document.querySelector(".btn-new-chat").click();
    });
  }

  /* ---------------- attachment preview ---------------- */

  imageInput && imageInput.addEventListener("change", function () {
    const file = imageInput.files[0];
    if (!file) return;
    pendingImageFile = file;
    renderAttachmentPreview();
  });

  function renderAttachmentPreview() {
    attachmentPreview.innerHTML = "";
    if (!pendingImageFile) return;
    const chip = document.createElement("div");
    chip.className = "attachment-chip";
    const img = document.createElement("img");
    img.src = URL.createObjectURL(pendingImageFile);
    const label = document.createElement("span");
    label.textContent = pendingImageFile.name.slice(0, 22);
    const remove = document.createElement("span");
    remove.className = "remove";
    remove.textContent = "✕";
    remove.addEventListener("click", function () {
      pendingImageFile = null;
      imageInput.value = "";
      renderAttachmentPreview();
    });
    chip.appendChild(img);
    chip.appendChild(label);
    chip.appendChild(remove);
    attachmentPreview.appendChild(chip);
  }

  /* ---------------- textarea behaviour ---------------- */

  if (messageInput) {
    messageInput.addEventListener("input", autoResize);
    messageInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        chatForm.requestSubmit();
      }
    });
  }

  /* ---------------- sending a message ---------------- */

  if (chatForm && conversationId) {
    chatForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const text = messageInput.value.trim();
      if (!text && !pendingImageFile) return;

      clearWelcome();

      const tempImageUrl = pendingImageFile ? URL.createObjectURL(pendingImageFile) : null;
      const userEl = buildMessageEl("user", text, { imageUrl: tempImageUrl });
      chatWindow.appendChild(userEl);
      scrollToBottom();

      const formData = new FormData();
      formData.append("message", text);
      if (pendingImageFile) formData.append("image", pendingImageFile);

      messageInput.value = "";
      autoResize();
      pendingImageFile = null;
      imageInput.value = "";
      renderAttachmentPreview();
      sendBtn.disabled = true;
      addTypingIndicator();

      fetch(T.sendUrlTemplate.replace("999999", conversationId), {
        method: "POST",
        headers: { "X-CSRFToken": T.csrfToken },
        body: formData,
      })
        .then((r) => r.json())
        .then((data) => {
          removeTypingIndicator();
          sendBtn.disabled = false;
          if (!data.ok) {
            alert(data.error || "Something went wrong.");
            return;
          }
          userEl.dataset.id = data.user_message.id;
          const titleEl = document.getElementById("chatTitle");
          if (titleEl) titleEl.textContent = data.conversation_title;
          const sidebarTitle = document.querySelector(
            '.chat-item-title[data-id="' + conversationId + '"]'
          );
          if (sidebarTitle) sidebarTitle.textContent = data.conversation_title;

          const assistantEl = buildMessageEl("assistant", data.assistant_message.content, {
            id: data.assistant_message.id,
          });
          chatWindow.appendChild(assistantEl);
          scrollToBottom();
        })
        .catch(() => {
          removeTypingIndicator();
          sendBtn.disabled = false;
          alert("Network error while talking to Tordi.");
        });
    });
  }

  /* ---------------- copy / edit message (delegated) ---------------- */

  chatWindow &&
    chatWindow.addEventListener("click", function (e) {
      const copyBtn = e.target.closest(".copy-btn");
      if (copyBtn) {
        const textEl = copyBtn.closest(".message-body").querySelector(".message-text");
        navigator.clipboard.writeText(textEl.dataset.raw || textEl.textContent);
        copyBtn.textContent = "✅ Copied";
        setTimeout(() => (copyBtn.textContent = "📋 Copy"), 1500);
        return;
      }

      const editBtn = e.target.closest(".edit-btn");
      if (editBtn) {
        const messageEl = editBtn.closest(".message");
        const textEl = messageEl.querySelector(".message-text");
        const currentText = textEl.dataset.raw || textEl.textContent;
        const newText = prompt("Edit your message:", currentText);
        if (newText === null || newText.trim() === "" || newText === currentText) return;

        const msgId = messageEl.dataset.id;
        addTypingIndicatorAfter(messageEl);

        fetch(T.editUrlTemplate.replace("999999", msgId), {
          method: "POST",
          headers: {
            "X-CSRFToken": T.csrfToken,
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: "message=" + encodeURIComponent(newText),
        })
          .then((r) => r.json())
          .then((data) => {
            removeTypingIndicator();
            if (!data.ok) {
              alert(data.error || "Could not edit message.");
              return;
            }
            textEl.dataset.raw = newText;
            textEl.innerHTML = escapeHtml(newText).replace(/\n/g, "<br>");
            // remove every message after this one, then append fresh reply
            let sibling = messageEl.nextElementSibling;
            while (sibling) {
              const toRemove = sibling;
              sibling = sibling.nextElementSibling;
              toRemove.remove();
            }
            const assistantEl = buildMessageEl("assistant", data.assistant_message.content, {
              id: data.assistant_message.id,
            });
            chatWindow.appendChild(assistantEl);
            scrollToBottom();
          })
          .catch(() => {
            removeTypingIndicator();
            alert("Network error while editing.");
          });
      }
    });

  function addTypingIndicatorAfter(el) {
    const indicator = document.createElement("div");
    indicator.className = "message assistant typing-indicator";
    indicator.id = "typingIndicator";
    indicator.innerHTML =
      '<div class="message-avatar">T</div>' +
      '<div class="message-body"><div class="message-text">' +
      '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>' +
      "</div></div>";
    el.after(indicator);
    scrollToBottom();
  }

  /* ---------------- sidebar: rename / delete / pin ---------------- */

  document.querySelectorAll(".rename-btn").forEach((btn) =>
    btn.addEventListener("click", function () {
      const id = btn.dataset.id;
      const titleEl = document.querySelector('.chat-item-title[data-id="' + id + '"]');
      const newTitle = prompt("Rename chat:", titleEl.textContent.trim());
      if (!newTitle) return;
      fetch(T.renameUrlTemplate.replace("999999", id), {
        method: "POST",
        headers: {
          "X-CSRFToken": T.csrfToken,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: "title=" + encodeURIComponent(newTitle),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.ok) {
            titleEl.textContent = data.title;
            const header = document.getElementById("chatTitle");
            if (header && conversationId === id) header.textContent = data.title;
          }
        });
    })
  );

  document.querySelectorAll(".delete-btn").forEach((btn) =>
    btn.addEventListener("click", function () {
      const id = btn.dataset.id;
      if (!confirm("Delete this chat permanently?")) return;
      fetch(T.deleteUrlTemplate.replace("999999", id), {
        method: "POST",
        headers: { "X-CSRFToken": T.csrfToken },
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.ok) {
            document.querySelector('.chat-item[data-id="' + id + '"]').remove();
            if (conversationId === id) window.location.href = "/";
          }
        });
    })
  );

  document.querySelectorAll(".pin-btn").forEach((btn) =>
    btn.addEventListener("click", function () {
      const id = btn.dataset.id;
      fetch(T.pinUrlTemplate.replace("999999", id), {
        method: "POST",
        headers: { "X-CSRFToken": T.csrfToken },
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.ok) window.location.reload();
        });
    })
  );

  /* ---------------- theme toggle ---------------- */

  const themeButtons = document.querySelectorAll(".theme-btn");
  function setActiveThemeButton(theme) {
    themeButtons.forEach((b) => b.classList.toggle("active", b.dataset.theme === theme));
  }
  setActiveThemeButton(document.documentElement.getAttribute("data-theme") || "dark");

  themeButtons.forEach((btn) =>
    btn.addEventListener("click", function () {
      const theme = btn.dataset.theme;
      document.documentElement.setAttribute("data-theme", theme);
      localStorage.setItem("tordi-theme", theme);
      setActiveThemeButton(theme);
      if (T.setThemeUrl) {
        fetch(T.setThemeUrl, {
          method: "POST",
          headers: {
            "X-CSRFToken": T.csrfToken,
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: "theme=" + theme,
        });
      }
    })
  );

  /* ---------------- sidebar collapse (mobile) ---------------- */

  const collapseBtn = document.getElementById("collapseSidebarBtn");
  const openBtn = document.getElementById("openSidebarBtn");
  collapseBtn && collapseBtn.addEventListener("click", () => sidebar.classList.toggle("collapsed"));
  openBtn && openBtn.addEventListener("click", () => sidebar.classList.remove("collapsed"));
  if (window.innerWidth <= 860) sidebar.classList.add("collapsed");

  /* ---------------- voice notes (Web Speech API) ---------------- */

  let recognition = null;
  let recording = false;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (micBtn) {
    if (!SpeechRecognition) {
      micBtn.title = "Voice input isn't supported in this browser (try Chrome).";
      micBtn.addEventListener("click", () =>
        alert("Voice input needs a browser that supports the Web Speech API, such as Chrome.")
      );
    } else {
      recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.continuous = false;
      recognition.interimResults = true;

      recognition.onstart = function () {
        recording = true;
        micBtn.classList.add("recording");
      };

      recognition.onresult = function (event) {
        let transcript = "";
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        messageInput.value = transcript;
        autoResize();
      };

      recognition.onerror = function () {
        recording = false;
        micBtn.classList.remove("recording");
      };

      recognition.onend = function () {
        recording = false;
        micBtn.classList.remove("recording");
      };

      micBtn.addEventListener("click", function () {
        if (recording) {
          recognition.stop();
        } else {
          try {
            recognition.start();
          } catch (err) {
            /* already started */
          }
        }
      });
    }
  }

  scrollToBottom();
})();
