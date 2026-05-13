frappe.ui.form.on("Customer", {
    custom_phone_number(frm){
        console.log("Cleaning phone number")
        if(!frm.doc.custom_phone_number)
            return;
        // Let's clean any space, dashes or parentheses or plus from the phone number
        let cleaned_number = frm.doc.custom_phone_number.replace(/[\s\-()+]/g, '');
        if (frm.doc.custom_phone_number !== cleaned_number) {
            frm.set_value("custom_phone_number", cleaned_number);
        }
    },
});