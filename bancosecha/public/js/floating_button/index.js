import Main from "./Main.vue";
import { createApp } from "vue";

frappe.provide("tzcode.FloatingButton");

class FloatingButton {
  constructor(actions = []) {
    // If you want to keep your hardcoded action, keep it here:
    // actions = [
    //   {
    //     label: "Reader Mode",
    //     handler(event) {
    //       console.log({ event });
    //     },
    //   },
    // ];

    this.actions = Array.isArray(actions) ? actions : [];

    this.app = null; // Vue app instance
    this.vm = null;  // Mounted component proxy (exposed API lives here)
    this._queue = []; // Calls made before mount

    this.make();
  }

  set_actions(actions = []) {
    this.actions = Array.isArray(actions) ? actions : [];
  }

  make() {
    // Create mount point
    const el = document.createElement("div");
    el.id = "floating-button";
    document.body.appendChild(el);

    // Create and mount Vue 3 app
    this.app = createApp(Main);
    this.vm = this.app.mount("#floating-button");

    // Seed initial actions after mount (Main exposes addAction)
    for (const action of this.actions) {
      this.vm.addAction(action);
    }

    // Flush any queued calls
    for (const fn of this._queue) fn();
    this._queue = [];
  }

  _runOrQueue(fn) {
    if (this.vm) fn();
    else this._queue.push(fn);
  }

  add(display, handler, route_sensitive = true) {
    this._runOrQueue(() => {
      this.vm.addAction({
        display,
        handler,
        routeSensitive: route_sensitive,
      });
    });
  }

  remove(label) {
    this._runOrQueue(() => {
      this.vm.removeActionByLabel(label);
    });
  }

  setupTree(tree) {
    this._runOrQueue(() => {
      this.vm.setupTree(tree);
    });
  }

  destroy() {
    // Optional, but nice hygiene if this ever needs teardown
    if (this.app) {
      this.app.unmount();
      this.app = null;
      this.vm = null;
    }
    const el = document.getElementById("floating-button");
    if (el) el.remove();
  }
}

tzcode.FloatingButton = FloatingButton;
export default FloatingButton;
