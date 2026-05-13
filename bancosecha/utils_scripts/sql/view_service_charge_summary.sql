DROP VIEW IF EXISTS `viewService Charge Summary`;
CREATE VIEW `viewService Charge Summary` AS
SELECT 
    `parent`,
    SUM(`amount`) AS `amount`
FROM
    `tabSales Invoice Item`
WHERE 
    `item_code` = 'Service Charge'
AND
    docstatus = 1
GROUP BY
    `parent`
