# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    def _variant_name(self, variable_attributes):
        return ", ".join(
            [v.name for v in self.sorted(key=lambda r: r.attribute_id.sequence)
             if v.attribute_id in variable_attributes])


class ProductProduct(models.Model):
    _inherit = 'product.product'

    var_desc = fields.Char(
        comment='Variant description',
        compute='_compute_var_desc',
        store=True
    )

    def name_get(self):

        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get(
                'default_code', False) or False
            if code:
                name = '[%s] %s' % (code, name)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(
                partner_id).commercial_partner_id.id]
        else:
            partner_ids = []

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []
        for product in self.sudo():
            # display all the attributes
            variable_attributes = product.attribute_line_ids.mapped(
                'attribute_id')
            variant = \
                product.product_template_attribute_value_ids._variant_name(
                    variable_attributes
                )

            name = variant and "%s (%s)" % (
                product.name, variant) or product.name
            sellers = []
            if partner_ids:
                sellers = [x for x in product.seller_ids if
                           (x.partner_id.id in partner_ids) and (
                                   x.product_id == product)]
                if not sellers:
                    sellers = [x for x in product.seller_ids if
                               (x.partner_id.id in partner_ids) and not x.product_id]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                            variant and "%s (%s)" % (
                        s.product_name, variant) or s.product_name
                    ) or False
                    mydict = {
                        'id': product.id,
                        'name': seller_variant or name,
                        'default_code': s.product_code or product.default_code,
                    }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                    'id': product.id,
                    'name': name,
                    'default_code': product.default_code,
                }
                result.append(_name_get(mydict))
        return result

    @api.model
    def name_search(self, name='', args=[], operator='ilike', limit=100):
        if not args:
            args = []
        products = None
        if name:
            if operator in ['like', 'ilike']:
                pieces = name.split(' ')
                search_domains = [('var_desc', operator, piece) for piece in
                                  pieces]
            else:
                search_domains = [('var_desc', operator, name)]
            products = self.search(search_domains)
            if products:
                return products.name_get()

        return super(ProductProduct, self).name_search(
            name=name, args=args,
            operator=operator,
            limit=limit
        )

    @api.depends('product_template_attribute_value_ids')
    def _compute_var_desc(self):
        for rec in self:
            idAndName = rec.name_get()[0]
            rec.var_desc = idAndName[1] if idAndName else None
