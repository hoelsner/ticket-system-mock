(function () {
  function getSideNavigation() {
    return document.querySelector("[data-side-navigation]");
  }

  function closeSideNavigation() {
    const sideNavigation = getSideNavigation();
    if (!sideNavigation?.open) {
      return;
    }

    sideNavigation.open = false;
    syncSideNavigationState();
  }

  function syncSideNavigationState() {
    const sideNavigation = getSideNavigation();
    document.body.classList.toggle("side-navigation-open", Boolean(sideNavigation?.open));
  }

  function initializeAppShell() {
    const sideNavigation = getSideNavigation();
    if (!sideNavigation) {
      return;
    }

    syncSideNavigationState();
    sideNavigation.addEventListener("toggle", syncSideNavigationState);

    document.addEventListener("click", function (event) {
      if (!sideNavigation.open) {
        return;
      }
      if (event.target.closest("[data-side-navigation]")) {
        return;
      }
      if (!event.target.closest("[data-app-content]")) {
        return;
      }

      event.preventDefault();
      closeSideNavigation();
    });

    document.addEventListener("click", function (event) {
      if (!event.target.closest("[data-side-navigation-close]")) {
        if (!event.target.closest("[data-side-navigation-dismiss]")) {
          return;
        }
      }

      closeSideNavigation();
    });

    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") {
        return;
      }

      closeSideNavigation();
    });
  }

  initializeAppShell();
}());
