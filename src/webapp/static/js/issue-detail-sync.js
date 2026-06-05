(function () {
  let detailStream = null;

  function getDetailPage() {
    return document.querySelector("[data-issue-detail-live]");
  }

  async function refreshDetailPage(detailPage) {
    const response = await fetch(detailPage.dataset.issueDetailRefreshUrl, {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    if (!response.ok) {
      throw new Error("Unable to refresh the issue detail page.");
    }

    const wrapper = document.createElement("div");
    wrapper.innerHTML = await response.text();
    const nextDetailPage = wrapper.firstElementChild;
    if (!nextDetailPage) {
      return;
    }

    detailPage.replaceWith(nextDetailPage);
    if (window.initializeIssueMarkdownEditors) {
      window.initializeIssueMarkdownEditors(nextDetailPage);
    }
  }

  function ensureDetailStream(detailPage) {
    if (detailStream || !detailPage?.dataset.issueDetailEventsUrl) {
      return;
    }

    detailStream = new EventSource(detailPage.dataset.issueDetailEventsUrl);
    detailStream.addEventListener("kanban.board.updated", function () {
      const currentDetailPage = getDetailPage();
      if (!currentDetailPage) {
        return;
      }

      refreshDetailPage(currentDetailPage).catch(function (error) {
        console.error(error);
      });
    });
  }

  function initializeIssueDetailSync() {
    const detailPage = getDetailPage();
    if (!detailPage) {
      return;
    }

    ensureDetailStream(detailPage);
  }

  document.addEventListener("DOMContentLoaded", initializeIssueDetailSync);
}());
