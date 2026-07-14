(function () {
  const TRIGGER_PATTERN = /\{\{\s*(user|issue|attachment)\s*:\s*([^}]*)$/i;
  const HELPER_TITLES = {
    user: "Mention a user",
    issue: "Reference an issue",
    attachment: "Link an attachment",
  };

  function getResultButtons(assist) {
    return Array.from(assist.querySelectorAll("[data-markdown-assist-option]"));
  }

  function setActiveResult(assist, index) {
    const buttons = getResultButtons(assist);
    if (!buttons.length) {
      assist.dataset.activeIndex = "-1";
      return;
    }

    const safeIndex = Math.max(0, Math.min(index, buttons.length - 1));
    assist.dataset.activeIndex = String(safeIndex);
    buttons.forEach(function (button, buttonIndex) {
      const isActive = buttonIndex === safeIndex;
      button.classList.toggle("markdown-editor__assist-option--active", isActive);
      button.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    buttons[safeIndex].scrollIntoView({ block: "nearest" });
  }

  function moveActiveResult(assist, offset) {
    const buttons = getResultButtons(assist);
    if (!buttons.length) {
      return;
    }

    const currentIndex = Number.parseInt(assist.dataset.activeIndex || "0", 10);
    const nextIndex = Number.isNaN(currentIndex) ? 0 : currentIndex + offset;
    setActiveResult(assist, nextIndex);
  }

  function activateCurrentResult(assist) {
    const buttons = getResultButtons(assist);
    if (!buttons.length) {
      return false;
    }

    const currentIndex = Number.parseInt(assist.dataset.activeIndex || "0", 10);
    const targetButton = buttons[Number.isNaN(currentIndex) ? 0 : currentIndex];
    if (!targetButton) {
      return false;
    }

    targetButton.click();
    return true;
  }

  function getCsrfToken(editor) {
    const configuredCookieName = editor?.dataset.csrfCookieName || "";
    if (configuredCookieName) {
      const cookies = document.cookie ? document.cookie.split(";") : [];
      for (const cookie of cookies) {
        const trimmed = cookie.trim();
        const separatorIndex = trimmed.indexOf("=");
        if (separatorIndex === -1) {
          continue;
        }

        const cookieName = trimmed.slice(0, separatorIndex);
        if (cookieName === configuredCookieName) {
          return decodeURIComponent(trimmed.slice(separatorIndex + 1));
        }
      }
    }

    const formTokenField = editor?.closest("form")?.querySelector('input[name="csrfmiddlewaretoken"]');
    if (formTokenField?.value) {
      return formTokenField.value;
    }

    const cookies = document.cookie ? document.cookie.split(";") : [];
    for (const cookie of cookies) {
      const trimmed = cookie.trim();
      const separatorIndex = trimmed.indexOf("=");
      if (separatorIndex === -1) {
        continue;
      }

      const cookieName = trimmed.slice(0, separatorIndex);
      if (cookieName === "csrftoken" || cookieName.endsWith("csrftoken")) {
        return decodeURIComponent(trimmed.slice(separatorIndex + 1));
      }
    }
    return "";
  }

  function debounce(callback, delay) {
    let timeoutId = null;
    return function debounced(...args) {
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(function () {
        callback.apply(null, args);
      }, delay);
    };
  }

  function updatePreview(editor) {
    const textarea = editor.querySelector("textarea");
    const preview = editor.querySelector("[data-markdown-preview]");
    if (!textarea || !preview) {
      return;
    }

    const body = new URLSearchParams({ body: textarea.value });
    fetch(editor.dataset.previewUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "X-CSRFToken": getCsrfToken(editor),
        "X-Requested-With": "XMLHttpRequest",
      },
      body: body.toString(),
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Preview failed.");
        }
        return response.json();
      })
      .then(function (payload) {
        preview.innerHTML = payload.html || "<p>No preview available.</p>";
      })
      .catch(function () {
        preview.innerHTML = "<p>Preview unavailable.</p>";
      });
  }

  function setUploadStatus(editor, message, isError) {
    const status = editor.querySelector("[data-markdown-upload-status]");
    if (!status) {
      return;
    }

    status.textContent = message || "";
    status.classList.toggle("markdown-editor__upload-status--error", Boolean(isError));
  }

  function insertTextAtCursor(textarea, text) {
    const currentValue = textarea.value;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    textarea.value = currentValue.slice(0, start) + text + currentValue.slice(end);
    textarea.selectionStart = start + text.length;
    textarea.selectionEnd = start + text.length;
  }

  function buildAttachmentInsertion(tokens) {
    return tokens.join("\n") + "\n";
  }

  function uploadDraftAttachments(editor, files) {
    const uploadUrl = editor.dataset.attachmentUploadUrl;
    const textarea = editor.querySelector("textarea");
    if (!uploadUrl || !textarea || !files.length) {
      return Promise.resolve();
    }

    const body = new FormData();
    Array.from(files).forEach(function (file) {
      body.append("files", file);
    });

    setUploadStatus(editor, "Uploading attachments...", false);
    return fetch(uploadUrl, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCsrfToken(editor),
        "X-Requested-With": "XMLHttpRequest",
      },
      body: body,
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Upload failed.");
        }
        return response.json();
      })
      .then(function (payload) {
        const attachments = payload.attachments || [];
        if (!attachments.length) {
          throw new Error("No attachments uploaded.");
        }

        insertTextAtCursor(
          textarea,
          buildAttachmentInsertion(
            attachments.map(function (attachment) {
              return attachment.token;
            })
          )
        );
        textarea.focus();
        updatePreview(editor);
        setUploadStatus(
          editor,
          attachments.length === 1
            ? "Attachment uploaded and inserted into the description."
            : "Attachments uploaded and inserted into the description.",
          false
        );
      })
      .catch(function () {
        setUploadStatus(editor, "Attachment upload failed.", true);
      });
  }

  function getSuggestionUrl(editor, helperType) {
    if (helperType === "user") {
      return editor.dataset.userSuggestionsUrl;
    }
    if (helperType === "issue") {
      return editor.dataset.issueSuggestionsUrl;
    }
    return editor.dataset.attachmentSuggestionsUrl;
  }

  function renderSuggestions(editor, helperType, results, replacementRange) {
    const assist = editor.querySelector("[data-markdown-assist]");
    const list = editor.querySelector("[data-markdown-assist-results]");
    const title = editor.querySelector("[data-markdown-assist-title]");
    const textarea = editor.querySelector("textarea");
    if (!assist || !list || !title || !textarea) {
      return;
    }

    title.textContent = HELPER_TITLES[helperType] || "Insert reference";
    assist.hidden = false;
    list.innerHTML = "";

    if (!results.length) {
      assist.dataset.activeIndex = "-1";
      list.innerHTML = "<li class=\"markdown-editor__assist-empty\">No matches found.</li>";
      return;
    }

    results.forEach(function (result) {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "secondary outline markdown-editor__assist-option";
      button.setAttribute("data-markdown-assist-option", "");
      button.setAttribute("aria-selected", "false");
      button.innerHTML = result.description
        ? "<strong>" + result.label + "</strong><span>" + result.description + "</span>"
        : "<strong>" + result.label + "</strong>";
      button.addEventListener("mouseenter", function () {
        setActiveResult(assist, results.indexOf(result));
      });
      button.addEventListener("click", function () {
        const currentValue = textarea.value;
        if (replacementRange) {
          textarea.value = currentValue.slice(0, replacementRange.start) + result.token + currentValue.slice(replacementRange.end);
          textarea.selectionStart = replacementRange.start + result.token.length;
          textarea.selectionEnd = replacementRange.start + result.token.length;
        } else {
          const start = textarea.selectionStart;
          const end = textarea.selectionEnd;
          textarea.value = currentValue.slice(0, start) + result.token + currentValue.slice(end);
          textarea.selectionStart = start + result.token.length;
          textarea.selectionEnd = start + result.token.length;
        }
        textarea.focus();
        assist.hidden = true;
        updatePreview(editor);
      });
      item.appendChild(button);
      list.appendChild(item);
    });

    setActiveResult(assist, 0);
  }

  function loadSuggestions(editor, helperType, query, replacementRange) {
    const suggestionUrl = getSuggestionUrl(editor, helperType);
    if (!suggestionUrl) {
      renderSuggestions(editor, helperType, [], replacementRange);
      return;
    }

    const url = new URL(suggestionUrl, window.location.origin);
    url.searchParams.set("query", query || "");

    fetch(url, {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Suggestion fetch failed.");
        }
        return response.json();
      })
      .then(function (payload) {
        renderSuggestions(editor, helperType, payload.results || [], replacementRange);
      })
      .catch(function () {
        renderSuggestions(editor, helperType, [], replacementRange);
      });
  }

  function handleTokenTrigger(editor) {
    const textarea = editor.querySelector("textarea");
    if (!textarea) {
      return;
    }

    const selectionStart = textarea.selectionStart;
    const textBeforeCursor = textarea.value.slice(0, selectionStart);
    const triggerMatch = textBeforeCursor.match(TRIGGER_PATTERN);
    if (!triggerMatch) {
      return;
    }

    const helperType = triggerMatch[1].toLowerCase();
    const query = triggerMatch[2].trim();
    loadSuggestions(editor, helperType, query, {
      start: selectionStart - triggerMatch[0].length,
      end: selectionStart,
    });
  }

  function initializeEditor(editor) {
    if (editor.dataset.markdownEditorReady === "true") {
      return;
    }

    const textarea = editor.querySelector("textarea");
    const assist = editor.querySelector("[data-markdown-assist]");
    const assistInput = editor.querySelector("[data-markdown-assist-input]");
    const assistCloseButton = editor.querySelector("[data-markdown-assist-close]");
    const uploadButton = editor.querySelector("[data-markdown-upload-button]");
    const uploadInput = editor.querySelector("[data-markdown-upload-input]");
    const previewUpdater = debounce(function () {
      updatePreview(editor);
    }, 250);

    if (!textarea || !assist || !assistInput || !assistCloseButton) {
      return;
    }

    function hideAssist(returnFocus) {
      assist.hidden = true;
      assist.dataset.activeIndex = "-1";
      if (returnFocus) {
        textarea.focus();
      }
    }

    function handleAssistNavigation(event) {
      if (assist.hidden) {
        return;
      }

      if (event.key === "ArrowDown") {
        event.preventDefault();
        moveActiveResult(assist, 1);
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        moveActiveResult(assist, -1);
        return;
      }
      if (event.key === "Enter") {
        if (activateCurrentResult(assist)) {
          event.preventDefault();
        }
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        hideAssist(true);
      }
    }

    editor.querySelectorAll("[data-markdown-helper-button]").forEach(function (button) {
      button.addEventListener("click", function () {
        const helperType = button.dataset.helperType;
        assist.hidden = false;
        assist.dataset.helperType = helperType;
        assistInput.value = "";
        assistInput.focus();
        loadSuggestions(editor, helperType, "", null);
      });
    });

    if (uploadButton && uploadInput) {
      uploadButton.addEventListener("click", function () {
        uploadInput.click();
      });
      uploadInput.addEventListener("change", function () {
        if (!uploadInput.files.length) {
          return;
        }
        uploadDraftAttachments(editor, uploadInput.files).finally(function () {
          uploadInput.value = "";
        });
      });
    }

    assistCloseButton.addEventListener("click", function () {
      hideAssist(true);
    });

    assistInput.addEventListener("input", function () {
      loadSuggestions(editor, assist.dataset.helperType || "user", assistInput.value.trim(), null);
    });
    assistInput.addEventListener("keydown", handleAssistNavigation);

    textarea.addEventListener("input", function () {
      previewUpdater();
      handleTokenTrigger(editor);
    });
    textarea.addEventListener("keydown", handleAssistNavigation);
    textarea.addEventListener("dragenter", function (event) {
      if (!editor.dataset.attachmentUploadUrl) {
        return;
      }
      event.preventDefault();
      editor.classList.add("markdown-editor--drag-over");
    });
    textarea.addEventListener("dragover", function (event) {
      if (!editor.dataset.attachmentUploadUrl) {
        return;
      }
      event.preventDefault();
      event.dataTransfer.dropEffect = "copy";
      editor.classList.add("markdown-editor--drag-over");
    });
    textarea.addEventListener("dragleave", function (event) {
      if (!editor.dataset.attachmentUploadUrl) {
        return;
      }
      if (event.currentTarget.contains(event.relatedTarget)) {
        return;
      }
      editor.classList.remove("markdown-editor--drag-over");
    });
    textarea.addEventListener("drop", function (event) {
      if (!editor.dataset.attachmentUploadUrl) {
        return;
      }
      event.preventDefault();
      editor.classList.remove("markdown-editor--drag-over");
      const files = Array.from(event.dataTransfer.files || []);
      if (!files.length) {
        return;
      }
      uploadDraftAttachments(editor, files);
    });

    updatePreview(editor);
    editor.dataset.markdownEditorReady = "true";
  }

  function initializeIssueMarkdownEditors(root) {
    const scope = root || document;
    scope.querySelectorAll("[data-markdown-editor]").forEach(initializeEditor);
  }

  window.initializeIssueMarkdownEditors = initializeIssueMarkdownEditors;
  document.addEventListener("DOMContentLoaded", function () {
    initializeIssueMarkdownEditors(document);
  });
}());
