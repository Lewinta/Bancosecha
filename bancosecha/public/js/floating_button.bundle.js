// import './floating_button/index.js';
import FloatingButton from "./floating_button";

frappe.provide("tzcode.floating_button");
tzcode.floating_button = new FloatingButton([
	// {
	// 	label: "Greet the World",
	// 	handler(event) {
	// 		console.log({ event });
	// 		frappe.msgprint("Hello World");
	// 	}
	// }
]);

frappe.call(
    "bancosecha.controllers.defaults.get_all_companies",
).then(function({ message }) {

    tzcode.floating_button.setupTree(message);
});

    {
    const { defaults } = frappe.boot.user;
	// Add current company to navbar

    const { company, cost_center } = defaults;

	let current_company = `
		<span class="ellipsis" style="max-width: 133px;">
            ${company}
        </span>
	`;

    if (
        cost_center
    ) {

        current_company += `
            <span class="ellipsis" style="max-width: 133px;">
              &nbsp;[${cost_center.split(" - ")[0]}]
            </span>
        `;
    }

	jQuery(document).ready(function() {
		jQuery(`
			div.main-section
			header.navbar.navbar-expand
			div.container
			div.collapse.navbar-collapse
			form.form-inline
		`).prepend(current_company);
	});
}