(function () {
  let boardStream = null;
  const columnOpenStates = {};
  const boardAnimationMediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

  function getCardSnapshots(boardShell) {
    const cardSnapshots = {};

    boardShell.querySelectorAll("[data-kanban-card-wrapper]").forEach((card) => {
      cardSnapshots[card.dataset.issueId] = {
        rect: card.getBoundingClientRect(),
        workflowState: card.dataset.workflowState,
      };
    });

    return cardSnapshots;
  }

  function animateMovedCards(boardShell, previousCardSnapshots) {
    if (!boardShell || boardAnimationMediaQuery.matches) {
      return;
    }

    boardShell.querySelectorAll("[data-kanban-card-wrapper]").forEach((card) => {
      const previousCardSnapshot = previousCardSnapshots[card.dataset.issueId];
      if (!previousCardSnapshot) {
        return;
      }

      const nextRect = card.getBoundingClientRect();
      const deltaX = previousCardSnapshot.rect.left - nextRect.left;
      const deltaY = previousCardSnapshot.rect.top - nextRect.top;
      const hasMoved = Math.abs(deltaX) > 1 || Math.abs(deltaY) > 1;
      const hasChangedColumn = previousCardSnapshot.workflowState !== card.dataset.workflowState;
      if (!hasMoved || !hasChangedColumn) {
        return;
      }

      card.animate([
        {
          transform: `translate(${deltaX}px, ${deltaY}px) scale(0.98)`,
          zIndex: "2",
          boxShadow: "0 1.1rem 2.4rem rgba(15, 23, 42, 0.18)",
        },
        {
          transform: "translate(0, 0) scale(1)",
          zIndex: "2",
          boxShadow: "0 0.35rem 1rem rgba(15, 23, 42, 0.08)",
        },
      ], {
        duration: 360,
        easing: "cubic-bezier(0.22, 1, 0.36, 1)",
      });
    });
  }

  function getColumnIssueCounts(boardShell) {
    const columnIssueCounts = {};

    boardShell.querySelectorAll("[data-kanban-column]").forEach((column) => {
      columnIssueCounts[column.dataset.workflowState] = Number.parseInt(column.dataset.issueCount || "0", 10) || 0;
    });

    return columnIssueCounts;
  }

  function getCsrfToken() {
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

  function getBoardShell() {
    return document.querySelector("[data-kanban-board-shell]");
  }

  async function persistColumnStates(boardShell) {
    if (!boardShell?.dataset.kanbanColumnStateUrl) {
      return;
    }

    await fetch(boardShell.dataset.kanbanColumnStateUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({states: columnOpenStates}),
    });
  }

  function snapshotColumnStates(boardShell) {
    boardShell.querySelectorAll("[data-kanban-column]").forEach((column) => {
      columnOpenStates[column.dataset.workflowState] = column.open;
    });
  }

  function restoreColumnStates(boardShell) {
    boardShell.querySelectorAll("[data-kanban-column]").forEach((column) => {
      const isOpen = columnOpenStates[column.dataset.workflowState];
      if (isOpen === false) {
        column.removeAttribute("open");
        return;
      }
      if (isOpen === true) {
        column.setAttribute("open", "");
      }
    });
  }

  function expandColumnsWithNewIssues(boardShell, previousIssueCounts) {
    let hasChanges = false;

    boardShell.querySelectorAll("[data-kanban-column]").forEach((column) => {
      const workflowState = column.dataset.workflowState;
      const previousIssueCount = previousIssueCounts[workflowState] || 0;
      const nextIssueCount = Number.parseInt(column.dataset.issueCount || "0", 10) || 0;

      if (previousIssueCount === 0 && nextIssueCount > 0) {
        columnOpenStates[workflowState] = true;
        hasChanges = true;
      }
    });

    return hasChanges;
  }

  function bindColumnStateListeners(boardShell) {
    boardShell.querySelectorAll("[data-kanban-column]").forEach((column) => {
      columnOpenStates[column.dataset.workflowState] = column.open;
      column.addEventListener("toggle", function () {
        columnOpenStates[column.dataset.workflowState] = column.open;
        persistColumnStates(boardShell).catch(function (error) {
          console.error(error);
        });
      });
    });
  }

  async function refreshBoard() {
    const boardShell = getBoardShell();
    if (!boardShell) {
      return;
    }

    snapshotColumnStates(boardShell);
    const previousCardSnapshots = getCardSnapshots(boardShell);
    const previousIssueCounts = getColumnIssueCounts(boardShell);

    const scrollLeft = boardShell.scrollLeft;
    const scrollTop = boardShell.scrollTop;

    const queryString = window.location.search;
    const response = await fetch(`${boardShell.dataset.kanbanFragmentUrl}${queryString}`, {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    if (!response.ok) {
      throw new Error("Unable to refresh the kanban board.");
    }

    const html = await response.text();
    boardShell.outerHTML = html;
    const nextBoardShell = getBoardShell();
    if (nextBoardShell) {
      const hasStateChanges = expandColumnsWithNewIssues(nextBoardShell, previousIssueCounts);
      restoreColumnStates(nextBoardShell);
      if (hasStateChanges) {
        persistColumnStates(nextBoardShell).catch(function (error) {
          console.error(error);
        });
      }
      window.requestAnimationFrame(function () {
        nextBoardShell.scrollLeft = scrollLeft;
        nextBoardShell.scrollTop = scrollTop;
        animateMovedCards(nextBoardShell, previousCardSnapshots);
      });
    }
    initializeBoard();
  }

  function ensureBoardStream(boardShell) {
    if (boardStream || !boardShell?.dataset.kanbanStreamUrl) {
      return;
    }

    boardStream = new EventSource(boardShell.dataset.kanbanStreamUrl);
    boardStream.addEventListener("kanban.board.updated", async function () {
      try {
        await refreshBoard();
      } catch (error) {
        console.error(error);
      }
    });
  }

  function createPlaceholder() {
    const placeholder = document.createElement("div");
    placeholder.className = "kanban-drop-placeholder";
    placeholder.setAttribute("data-kanban-drop-placeholder", "true");
    return placeholder;
  }

  function findInsertionPoint(container, y, draggedCard, placeholder) {
    const cards = Array.from(container.querySelectorAll("[data-kanban-card-wrapper]"))
      .filter((card) => card !== draggedCard && card !== placeholder);

    return cards.find((card) => {
      const box = card.getBoundingClientRect();
      return y < box.top + box.height / 2;
    });
  }

  function getPriorityPositionIndex(container, draggedCard, placeholder) {
    const draggedPriority = draggedCard.dataset.priority;
    let positionIndex = 0;
    for (const child of Array.from(container.children)) {
      if (child === placeholder) {
        break;
      }
      if (
        child !== draggedCard
        && child.matches("[data-kanban-card-wrapper]")
        && child.dataset.priority === draggedPriority
      ) {
        positionIndex += 1;
      }
    }
    return positionIndex;
  }

  function bindBoardInteractions(boardShell) {
    const placeholder = createPlaceholder();
    let draggedCard = null;
    let sourceContainer = null;
    let sourceNextSibling = null;

    boardShell.querySelectorAll("[data-kanban-card-wrapper]").forEach((card) => {
      card.addEventListener("dragstart", function (event) {
        draggedCard = card;
        sourceContainer = card.parentElement;
        sourceNextSibling = card.nextElementSibling;
        card.classList.add("kanban-card-wrapper--dragging");
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", card.dataset.issueId);
      });

      card.addEventListener("dragend", function () {
        card.classList.remove("kanban-card-wrapper--dragging", "kanban-card-wrapper--pending");
        placeholder.remove();
        draggedCard = null;
        sourceContainer = null;
        sourceNextSibling = null;
      });
    });

    boardShell.querySelectorAll("[data-kanban-column-body]").forEach((columnBody) => {
      columnBody.addEventListener("dragover", function (event) {
        if (!draggedCard) {
          return;
        }
        event.preventDefault();
        const beforeNode = findInsertionPoint(columnBody, event.clientY, draggedCard, placeholder);
        if (beforeNode) {
          columnBody.insertBefore(placeholder, beforeNode);
          return;
        }
        columnBody.appendChild(placeholder);
      });

      columnBody.addEventListener("drop", async function (event) {
        if (!draggedCard) {
          return;
        }
        event.preventDefault();

        const targetState = columnBody.dataset.workflowState;
        const positionIndex = getPriorityPositionIndex(columnBody, draggedCard, placeholder);
        const moveUrl = draggedCard.dataset.moveUrl;

        columnBody.insertBefore(draggedCard, placeholder);
        placeholder.remove();
        draggedCard.classList.add("kanban-card-wrapper--pending");

        try {
          const response = await fetch(moveUrl, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCsrfToken(),
              "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify({
              target_state: targetState,
              position_index: positionIndex,
            }),
          });

          if (!response.ok) {
            throw new Error("Unable to move the issue on the kanban board.");
          }
        } catch (error) {
          console.error(error);
          if (sourceContainer) {
            if (sourceNextSibling) {
              sourceContainer.insertBefore(draggedCard, sourceNextSibling);
            } else {
              sourceContainer.appendChild(draggedCard);
            }
          }
          draggedCard.classList.remove("kanban-card-wrapper--pending");
          try {
            await refreshBoard();
          } catch (refreshError) {
            console.error(refreshError);
          }
        }
      });
    });
  }

  function initializeBoard() {
    const boardShell = getBoardShell();
    if (!boardShell) {
      return;
    }

    ensureBoardStream(boardShell);
    restoreColumnStates(boardShell);
    bindColumnStateListeners(boardShell);
    bindBoardInteractions(boardShell);
  }

  document.addEventListener("DOMContentLoaded", initializeBoard);
}());
