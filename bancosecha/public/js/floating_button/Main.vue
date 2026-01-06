<template>
  <div
    v-if="showButtonGroup"
    class="btn-group"
    role="group"
    aria-label="Switch between companies"
  >
    <div
      class="btn-group"
      role="group"
      style="position: fixed; bottom: 15px; right: 25px; z-index: 999"
    >
      <!-- Main button -->
      <button
        id="floating_button"
        type="button"
        class="btn btn-primary icon-btn"
        data-toggle="dropdown"
        aria-haspopup="true"
        aria-expanded="false"
        style="
          border-radius: 50%;
          width: 50px;
          height: 50px;
          outline: none;
          box-shadow: rgb(0 0 0 / 43%) 3px 3px 7px 0px;
        "
      >
        <span class="menu-btn-group-label" data-label="">
          <svg class="icon icon-sm">
            <use href="#icon-change"></use>
          </svg>
        </span>
      </button>

      <!-- Submenu -->
      <div
        v-if="treeData === null"
        class="dropdown-menu"
        aria-labelledby="floating_button"
      >
        <li v-for="d in actions" :key="d.label">
          <a
            class="dropdown-item"
            href="#"
            :class="getCssClass(d)"
            @click.prevent="handleClick(d, $event)"
          >
            {{ d.label }}
          </a>
        </li>
      </div>

      <div
        v-else
        class="dropdown-menu"
        aria-labelledby="floating_button"
      >
        <li v-for="company in Object.keys(treeData)" :key="company">
          <span
            class="dropdown-item"
            style="font-weight: bold; color: black;"
            @click.prevent
          >
            {{ company }}

            <p v-for="cc in treeData[company]" :key="cc">
              <a
                class="dropdown-item"
                href="#"
                :class="obtainCssClass(cc)"
                @click.prevent="onClick(company, cc)"
                style="font-weight: normal; color: black;"
              >
                - {{ cc }}
              </a>
            </p>
          </span>
        </li>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, defineExpose } from "vue";

const treeData = ref(null);
const actions = ref([]);

const showButtonGroup = computed(() => {
  return (actions.value?.length > 0) || treeData.value !== null;
});

function onClick(company, cost_center) {
  const method =
    "frappe.core.doctype.session_default_settings.session_default_settings.set_session_default_values";

  const args = {
    default_values: {
      company,
      cost_center,
    },
  };

  function callback() {
    frappe.assets.clear_local_storage();
    location.reload(true);
  }

  frappe.call({ method, args, callback });
}

function handleClick(action, evt) {
  // evt already prevented by @click.prevent
  if (action?.handler) {
    action.handler(evt);
  }
}

function addAction(action) {
  const display = action?.display || {};
  const label = display?.name ?? action?.label;
  const company = display?.company ?? action?.company;

  if (!label) {
    frappe.throw("Name is required");
  }

  // normalize action so template + class functions always have label
  const normalized = { ...action, label, company, display };

  const idx = actions.value.findIndex((a) => a.label === label);
  if (idx !== -1) {
    actions.value.splice(idx, 1);
  }
  actions.value.push(normalized);

  // keep compatibility with existing external code that expects prevCompany
  setTimeout(() => {
    try {
      // eslint-disable-next-line no-undef
      prevCompany = company;
    } catch (_) {
      // ignore if prevCompany isn't defined globally
    }
  }, 1);
}

function removeActionByLabel(label) {
  const idx = actions.value.findIndex((a) => a.label === label);
  if (idx !== -1) actions.value.splice(idx, 1);
}

function clearRouteSensitiveActions() {
  actions.value = actions.value.filter((a) => !a.routeSensitive);
}

function getCssClass({ label }) {
  return {
    active: frappe?.boot?.user?.defaults?.company === label,
  };
}

function obtainCssClass(cost_center) {
  return {
    active: frappe?.boot?.user?.defaults?.cost_center === cost_center,
  };
}

function setupTree(data) {
  treeData.value = data;
}

const routeChangeHandler = () => clearRouteSensitiveActions();

onMounted(() => {
  if (frappe?.router?.on) {
    frappe.router.on("change", routeChangeHandler);
  }
});

onBeforeUnmount(() => {
  // Frappe router may or may not implement off()
  if (frappe?.router?.off) {
    frappe.router.off("change", routeChangeHandler);
  }
});

// If other scripts call methods on this Vue component instance, expose them.
defineExpose({
  addAction,
  removeActionByLabel,
  clearRouteSensitiveActions,
  setupTree,
});
</script>

<style>
/* Add CSS for submenu */
.dropdown-menu {
  display: none;
  position: absolute;
  background-color: var(--gray-400);
  color: var(--text-color) !important;
  min-width: 160px;
  box-shadow: 0 8px 16px 0 rgba(0, 0, 0, 0.2);
  z-index: 1;
}

/* Bootstrap toggles .show on dropdown-menu */
.dropdown-menu.show {
  display: block;
}

.dropdown-item {
  padding: 12px 16px;
  text-decoration: none;
  display: block;
}

.dropdown-item:hover {
  background-color: var(--gray-400);
}

.active {
  background-color: var(--bg-color);
}
</style>
