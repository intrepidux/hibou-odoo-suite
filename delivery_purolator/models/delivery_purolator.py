from odoo import fields, models, _
from odoo.exceptions import UserError
from .purolator_services import PurolatorClient
import logging


_logger = logging.getLogger(__name__)

PUROLATOR_SERVICES = [
    ('PurolatorExpress9AM', 'Purolator Express 9AM'),
    ('PurolatorExpress10:30AM', 'Purolator Express 10:30AM'),
    ('PurolatorExpress12PM', 'Purolator Express 12PM'),
    ('PurolatorExpress', 'Purolator Express'),
    ('PurolatorExpressEvening', 'Purolator Express Evening'),
    ('PurolatorExpressEnvelope9AM', 'Purolator Express Envelope 9AM'),
    ('PurolatorExpressEnvelope10:30AM', 'Purolator Express Envelope 10:30AM'),
    ('PurolatorExpressEnvelope12PM', 'Purolator Express Envelope 12PM'),
    ('PurolatorExpressEnvelope', 'Purolator Express Envelope'),
    ('PurolatorExpressEnvelopeEvening', 'Purolator Express Envelope Evening'),
    ('PurolatorExpressPack9AM', 'Purolator Express Pack 9AM'),
    ('PurolatorExpressPack10:30AM', 'Purolator Express Pack 10:30AM'),
    ('PurolatorExpressPack12PM', 'Purolator Express Pack 12PM'),
    ('PurolatorExpressPack', 'Purolator Express Pack'),
    ('PurolatorExpressPackEvening', 'Purolator Express Pack Evening'),
    ('PurolatorExpressBox9AM', 'Purolator Express Box 9AM'),
    ('PurolatorExpressBox10:30AM', 'Purolator Express Box 10:30AM'),
    ('PurolatorExpressBox12PM', 'Purolator Express Box 12PM'),
    ('PurolatorExpressBox', 'Purolator Express Box'),
    ('PurolatorExpressBoxEvening', 'Purolator Express Box Evening'),
    ('PurolatorGround', 'Purolator Ground'),
    ('PurolatorGround9AM', 'Purolator Ground 9AM'),
    ('PurolatorGround10:30AM', 'Purolator Ground 10:30AM'),
    ('PurolatorGroundEvening', 'Purolator Ground Evening'),
    ('PurolatorQuickShip', 'Purolator Quick Ship'),
    ('PurolatorQuickShipEnvelope', 'Purolator Quick Ship Envelope'),
    ('PurolatorQuickShipPack', 'Purolator Quick Ship Pack'),
    ('PurolatorQuickShipBox', 'Purolator Quick Ship Box'),
    ('PurolatorExpressU.S.', 'Purolator Express U.S.'),
    ('PurolatorExpressU.S.9AM', 'Purolator Express U.S. 9AM'),
    ('PurolatorExpressU.S.10:30AM', 'Purolator Express U.S. 10:30AM'),
    ('PurolatorExpressU.S.12:00', 'Purolator Express U.S. 12:00'),
    ('PurolatorExpressEnvelopeU.S.', 'Purolator Express Envelope U.S.'),
    ('PurolatorExpressU.S.Envelope9AM', 'Purolator Express U.S. Envelope 9AM'),
    ('PurolatorExpressU.S.Envelope10:30AM', 'Purolator Express U.S. Envelope 10:30AM'),
    ('PurolatorExpressU.S.Envelope12:00', 'Purolator Express U.S. Envelope 12:00'),
    ('PurolatorExpressPackU.S.', 'Purolator Express Pack U.S.'),
    ('PurolatorExpressU.S.Pack9AM', 'Purolator Express U.S. Pack 9AM'),
    ('PurolatorExpressU.S.Pack10:30AM', 'Purolator Express U.S. Pack 10:30AM'),
    ('PurolatorExpressU.S.Pack12:00', 'Purolator Express U.S. Pack 12:00'),
    ('PurolatorExpressBoxU.S.', 'Purolator Express Box U.S.'),
    ('PurolatorExpressU.S.Box9AM', 'Purolator Express U.S. Box 9AM'),
    ('PurolatorExpressU.S.Box10:30AM', 'Purolator Express U.S. Box 10:30AM'),
    ('PurolatorExpressU.S.Box12:00', 'Purolator Express U.S. Box 12:00'),
    ('PurolatorGroundU.S.', 'Purolator Ground U.S.'),
    ('PurolatorExpressInternational', 'Purolator Express International'),
    ('PurolatorExpressInternational9AM', 'Purolator Express International 9AM'),
    ('PurolatorExpressInternational10:30AM', 'Purolator Express International 10:30AM'),
    ('PurolatorExpressInternational12:00', 'Purolator Express International 12:00'),
    ('PurolatorExpressEnvelopeInternational', 'Purolator Express Envelope International'),
    ('PurolatorExpressInternationalEnvelope9AM', 'Purolator Express International Envelope 9AM'),
    ('PurolatorExpressInternationalEnvelope10:30AM', 'Purolator Express International Envelope 10:30AM'),
    ('PurolatorExpressInternationalEnvelope12:00', 'Purolator Express International Envelope 12:00'),
    ('PurolatorExpressPackInternational', 'Purolator Express Pack International'),
    ('PurolatorExpressInternationalPack9AM', 'Purolator Express International Pack 9AM'),
    ('PurolatorExpressInternationalPack10:30AM', 'Purolator Express International Pack 10:30AM'),
    ('PurolatorExpressInternationalPack12:00', 'Purolator Express International Pack 12:00'),
    ('PurolatorExpressBoxInternational', 'Purolator Express Box International'),
    ('PurolatorExpressInternationalBox9AM', 'Purolator Express International Box 9AM'),
    ('PurolatorExpressInternationalBox10:30AM', 'Purolator Express International Box 10:30AM'),
    ('PurolatorExpressInternationalBox12:00', 'Purolator Express International Box 12:00'),
]


class ProviderPurolator(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('purolator', 'Purolator')], 
                                     ondelete={'purolator': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})
    purolator_api_key = fields.Char(string='Purolator API Key', groups='base.group_system')
    purolator_password = fields.Char(string='Purolator Password', groups='base.group_system')
    purolator_activation_key = fields.Char(string='Purolator Activation Key', groups='base.group_system')
    purolator_account_number = fields.Char(string='Purolator Account Number', groups='base.group_system')
    purolator_service_type = fields.Selection(selection=PUROLATOR_SERVICES,
                                              default='PurolatorGround')
    purolator_default_package_type_id = fields.Many2one('stock.package.type', string="Purolator Package Type")
    purolator_label_file_type = fields.Selection([
            ('PDF', 'PDF'),
            ('ZPL', 'ZPL'),
        ], default='ZPL', string="Purolator Label File Type")
    
    def purolator_convert_weight(self, weight):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_lb'), round=False)
    
    def purolator_convert_length(self, length):
        volume_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_lb'), round=False)

    def purolator_rate_shipment(self, order):
        # sudoself = self.sudo()
        third_party = self.purolator_third_party(order=order)
        sender = self.get_shipper_warehouse(order=order)
        receiver = self.get_recipient(order=order)
        receiver_address = {
            'City': receiver.city,
            'Province': receiver.state_id.code,
            'Country': receiver.country_id.code,
            'PostalCode': receiver.zip,
        }
        # TODO packaging volume/length/width/height
        weight = self.purolator_convert_weight(order._get_estimated_weight())
        service = self._purolator_service()
        res = service.get_quick_estimate(
            sender.zip,
            receiver_address,
            self.purolator_default_package_type_id.shipper_package_code,
            weight,
        )
        if res['error']:
            return {
                'success': False,
                'price': 0.0,
                'error_message': _(res['error']),
                'warning_message': False,
            }
        shipment = list(filter(lambda s: s['ServiceID'] == self.purolator_service_type, res['shipments']))
        if not shipment:
            return {
                'success': False,
                'price': 0.0,
                'error_message': _('No rate found matching service: %s') % self.purolator_service_type,
                'warning_message': False,
            }
        return {
            'success': True, 
            'price': shipment[0]['TotalPrice'] if not third_party else 0.0,
            'error_message': False,
            'warning_message': False,
        }
    
    def purolator_rate_shipment_multi(self, order=None, picking=None, packages=None):
        if not packages:
            return self._purolator_rate_shipment_multi_package(order=order, picking=picking)
        else:
            rates = []
            for package in packages:
                rates += self._purolator_rate_shipment_multi_package(order=order, picking=picking, package=package)
            return rates
    
    def _purolator_rate_shipment_multi_package(self, order=None, picking=None, package=None):
        third_party = self.purolator_third_party(order=order, picking=picking)
        sender = self.get_shipper_warehouse(order=order, picking=picking)
        receiver = self.get_recipient(order=order, picking=picking)
        receiver_address = {
            'City': receiver.city,
            'Province': receiver.state_id.code,
            'Country': receiver.country_id.code,
            'PostalCode': receiver.zip,
        }
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        volume_uom_id = self.env['product.template']._get_volume_uom_id_from_ir_config_parameter()
        
        date_planned = fields.Datetime.now()
        if self.env.context.get('date_planned'):
            date_planned = self.env.context.get('date_planned')
        
        # TODO need packaging volume/dimensions
        package_code = self.purolator_default_package_type_id.shipper_package_code
        if order:
            weight = order._get_estimated_weight()
        else:
            if package:
                weight = package.shipping_weight
                package_code = package.package_type_id.shipper_package_code if package.package_type_id.package_carrier_type == 'purolator' else package_code
            else:
                weight = picking.shipping_weight or picking.weight
        weight = self.purolator_convert_weight(weight)
        service = self._purolator_service()
        res = service.get_quick_estimate(sender.zip, receiver_address, package_code, weight)
        if res['error']:
            return [{'carrier': self,
                     'success': False,
                     'price': 0.0,
                     'error_message': _('Error:\n%s') % res['error'],
                     'warning_message': False,
                    }]
        rates = []
        for shipment in res['shipments']:
            carrier = self.purolator_find_delivery_carrier_for_service(shipment['ServiceID'])
            if carrier:
                price = shipment['TotalPrice']
                rates.append({
                    'carrier': carrier,
                    'package': package or self.env['stock.quant.package'].browse(),
                    'success': True,
                    'price': price if not third_party else 0.0,
                    'error_message': False,
                    'warning_message': _('TotalCharge not found.') if price == 0.0 else False,
                    'date_planned': date_planned,
                    'date_delivered': fields.Date.to_date(shipment['ExpectedDeliveryDate']),
                    'transit_days': shipment['EstimatedTransitDays'],
                    'service_code': shipment['ServiceID'],
                })
            
        return rates
    
    def purolator_find_delivery_carrier_for_service(self, service_code):
        if self.purolator_service_type == service_code:
            return self
        carrier = self.search([('delivery_type', '=', 'purolator'),
                               ('purolator_service_type', '=', service_code),
                               ('purolator_account_number', '=', self.purolator_account_number),
                               ], limit=1)
        return carrier
    
    def purolator_third_party(self, order=None, picking=None):
        third_party_account = self.get_third_party_account(order=order, picking=picking)
        if third_party_account:
            if not third_party_account.delivery_type == 'purolator':
                raise ValidationError('Non-Purolator Shipping Account indicated during Purolator shipment.')
            return third_party_account.name
        return False
    
    def _purolator_service(self):
        return PurolatorClient(
            self.purolator_api_key,
            self.purolator_password,
            self.purolator_activation_key,
            self.purolator_account_number,
            self.prod_environment,
        )

    def _purolator_address_street(self, partner):
        # assume we don't have base_address_extended
        street = partner.street or ''
        street_pieces = [t.strip() for t in street.split(' ')]
        len_street_pieces = len(street_pieces)
        if len_street_pieces >= 3:
            street_num = street_pieces[0]
            street_type = street_pieces[2]
            # TODO santize the types?  I see an example for "Douglas Road" that sends "Street"
            return street_num, ' '.join(street_pieces[1:]), 'Street'
        elif len_street_pieces == 2:
            return street_pieces[0], street_pieces[1], 'Street'
        return '', street, 'Street'

    def _purolator_address_phonenumber(self, partner):
        # TODO parse out of partner.phone or one of the many other phone numbers
        return '1', '905', '5555555'
        

    def _purolator_fill_address(self, addr, partner):
        addr.Name = partner.name if not partner.is_company else ''
        addr.Company = partner.name if partner.is_company else (partner.company_name or '')
        addr.Department = ''
        addr.StreetNumber, addr.StreetName, addr.StreetType = self._purolator_address_street(partner)
        # addr.City = partner.city.upper() if partner.city else ''
        addr.City = partner.city or ''
        addr.Province = partner.state_id.code
        addr.Country = partner.country_id.code
        addr.PostalCode = partner.zip
        addr.PhoneNumber.CountryCode, addr.PhoneNumber.AreaCode, addr.PhoneNumber.Phone = self._purolator_address_phonenumber(partner)
    
    def _purolator_extract_doc_blobs(self, documents_result):
        res = []
        for d in getattr(documents_result.Documents, 'Document', []):
            for d2 in getattr(d.DocumentDetails, 'DocumentDetail', []):
                res.append(d2.Data)
        return res

    # Picking Shipping
    def purolator_send_shipping(self, pickings):
        res = []
        service = self._purolator_service()

        for picking in pickings:
            picking_packages = self.get_to_ship_picking_packages(picking)
            if picking_packages is None:
                continue
            
            shipment = service.shipment_request()
            
            # populate origin information
            sender = self.get_shipper_warehouse(picking=picking)
            self._purolator_fill_address(shipment.SenderInformation.Address, sender)
            
            receiver = self.get_recipient(picking=picking)
            self._purolator_fill_address(shipment.ReceiverInformation.Address, receiver)
            
            service.shipment_add_picking_packages(shipment, self, picking, picking_packages)
            
            # TODO package level signature and insurance....
            # IF we cannot do this at the package level, then we must implement it here.
            # We may need to warn that all packages will follow the same rule.
            # //Define OptionsInformation
            # //ResidentialSignatureDomestic
            # $request->Shipment->PackageInformation->OptionsInformation->Options->OptionIDValuePair->ID = "ResidentialSignatureDomestic";
            # $request->Shipment->PackageInformation->OptionsInformation->Options->OptionIDValuePair->Value = "true";
            
            shipment.PaymentInformation.PaymentType = 'Sender'
            shipment.PaymentInformation.RegisteredAccountNumber = self.purolator_account_number
            shipment.PaymentInformation.BillingAccountNumber = self.purolator_account_number
            third_party_account = self.purolator_third_party(picking=picking)
            # when would it be 'Receiver' ?
            if third_party_account:
                shipment.PaymentInformation.PaymentType = 'ThirdParty'
                shipment.PaymentInformation.BillingAccountNumber = third_party_account
            
            shipment_res = service.shipment_create(shipment,
                                                   printer_type=('Regular' if self.purolator_label_file_type == 'PDF' else 'Thermal'))
            # _logger.info('purolator service.shipment_create for shipment %s resulted in %s' % (shipment, shipment_res))
            
            errors = shipment_res.ResponseInformation.Errors
            if errors:
                errors = errors.Error  # unpack container node
                puro_errors = '\n\n'.join(['%s - %s - %s' % (e.Code, e.AdditionalInformation, e.Description) for e in errors])
                raise UserError(_('Error(s) during Purolator Shipment Request:\n%s') % (puro_errors, ))
            
            document_blobs = []
            shipment_pin = shipment_res.ShipmentPIN.Value
            if picking_packages and getattr(shipment_res, 'PiecePINs', None):
                piece_pins = shipment_res.PiecePINs.PIN
                for p, pin in zip(picking_packages, piece_pins):
                    pin = pin.Value
                    p.carrier_tracking_ref = pin
                    doc_res = service.document_by_pin(pin, output_type=self.purolator_label_file_type)
                    for n, blob in enumerate(self._purolator_extract_doc_blobs(doc_res), 1):
                        document_blobs.append(('PuroPackage-%s-%s.%s' % (pin, n, self.purolator_label_file_type), blob))
            else:
                # retrieve shipment_pin document(s)
                doc_res = service.document_by_pin(shipment_pin, output_type=self.purolator_label_file_type)
                # _logger.info('purolator service.document_by_pin for pin %s resulted in %s' % (shipment_pin, doc_res))
                for n, blob in enumerate(self._purolator_extract_doc_blobs(doc_res), 1):
                    document_blobs.append(('PuroShipment-%s-%s.%s' % (shipment_pin, n, self.purolator_label_file_type), blob))
                
            if document_blobs:
                logmessage = _("Shipment created in Purolator <br/> <b>Tracking Number/PIN : </b>%s") % (shipment_pin)
                picking.message_post(body=logmessage, attachments=document_blobs)
            
            picking.carrier_tracking_ref = shipment_pin
            shipping_data = {
                'exact_price': 0.0,  # TODO How can we know?!
                'tracking_number': shipment_pin,
            }
            res.append(shipping_data)
        
        return res
