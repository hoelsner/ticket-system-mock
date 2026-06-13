(function () {
  function parseTemplateData() {
    const dataElement = document.getElementById("issue-description-template-data");
    if (!dataElement) {
      return [];
    }

    try {
      return JSON.parse(dataElement.textContent || "[]");
    } catch {
      return [];
    }
  }

  function matchesScope(template, collectionId, categoryId) {
    if (template.collection_id && template.collection_id !== collectionId) {
      return false;
    }
    if (template.category_id && template.category_id !== categoryId) {
      return false;
    }
    return true;
  }

  function syncTemplateOptions(select, templatesById, collectionSelect, categorySelect) {
    const collectionId = collectionSelect ? collectionSelect.value : "";
    const categoryId = categorySelect ? categorySelect.value : "";
    let selectedOptionIsValid = !select.value;

    Array.from(select.options).forEach(function (option) {
      if (!option.value) {
        option.hidden = false;
        option.disabled = false;
        return;
      }

      const template = templatesById.get(option.value);
      const isEligible = Boolean(template) && matchesScope(template, collectionId, categoryId);
      option.hidden = !isEligible;
      option.disabled = !isEligible;
      if (option.value === select.value && isEligible) {
        selectedOptionIsValid = true;
      }
    });

    if (!selectedOptionIsValid) {
      select.value = "";
    }
  }

  function applyTemplate(select, templatesById, descriptionField) {
    const template = templatesById.get(select.value);
    if (!template || !descriptionField) {
      return;
    }

    descriptionField.value = template.description_markdown;
    descriptionField.dispatchEvent(new Event("input", { bubbles: true }));
    descriptionField.focus();
  }

  function initializeIssueDescriptionTemplateSelector(root) {
    const scope = root || document;
    const templateSelect = scope.querySelector("select[name='description_template']");
    const collectionSelect = scope.querySelector("select[name='collection']");
    const categorySelect = scope.querySelector("select[name='category']");
    const descriptionField = scope.querySelector("textarea[name='description_markdown']");
    const templates = parseTemplateData();

    if (!templateSelect || !descriptionField || !templates.length) {
      return;
    }

    const templatesById = new Map(
      templates.map(function (template) {
        return [template.id, template];
      })
    );

    function syncOptions() {
      syncTemplateOptions(templateSelect, templatesById, collectionSelect, categorySelect);
    }

    if (collectionSelect) {
      collectionSelect.addEventListener("change", syncOptions);
    }
    if (categorySelect) {
      categorySelect.addEventListener("change", syncOptions);
    }
    templateSelect.addEventListener("change", function () {
      applyTemplate(templateSelect, templatesById, descriptionField);
    });

    syncOptions();
  }

  document.addEventListener("DOMContentLoaded", function () {
    initializeIssueDescriptionTemplateSelector(document);
  });
}());
