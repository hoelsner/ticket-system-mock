(function () {
  function getModal() {
    return document.querySelector("[data-issue-detail-modal]");
  }

  function getModalSurface() {
    return document.querySelector("[data-issue-detail-modal-surface]");
  }

  function buildModalUrl(baseUrl) {
    const url = new URL(baseUrl, window.location.origin);
    url.searchParams.set("modal", "1");
    return url.toString();
  }

  async function openIssueModal(url) {
    const modal = getModal();
    const surface = getModalSurface();
    if (!modal || !surface) {
      return;
    }

    surface.innerHTML = '<p class="issue-detail-modal__loading">Loading issue details...</p>';
    if (!modal.open) {
      modal.showModal();
    }

    const response = await fetch(buildModalUrl(url), {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    if (!response.ok) {
      surface.innerHTML = '<p class="issue-detail-modal__error">Unable to load issue details.</p>';
      return;
    }

    surface.innerHTML = await response.text();
    if (window.initializeIssueMarkdownEditors) {
      window.initializeIssueMarkdownEditors(surface);
    }
  }

  document.addEventListener("click", function (event) {
    const closeButton = event.target.closest("[data-issue-detail-modal-close]");
    if (closeButton) {
      const modal = getModal();
      if (modal) {
        modal.close();
      }
      return;
    }

    const trigger = event.target.closest("[data-issue-modal-trigger]");
    if (!trigger) {
      return;
    }
    if (trigger.closest("[data-issue-detail-page]")) {
      return;
    }
    if (event.defaultPrevented || event.button !== 0) {
      return;
    }
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }

    event.preventDefault();
    openIssueModal(trigger.dataset.issueModalUrl || trigger.href).catch(function (error) {
      console.error(error);
      window.location.href = trigger.href;
    });
  });

  document.addEventListener("click", function (event) {
    const modal = getModal();
    if (!modal || event.target !== modal) {
      return;
    }
    modal.close();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") {
      return;
    }
    const modal = getModal();
    if (modal?.open) {
      modal.close();
    }
  });
}());
