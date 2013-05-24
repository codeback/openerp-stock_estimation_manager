from openerp.osv import fields,osv

class stock_estimation_config_settings(osv.osv_memory):   
    _name = "stock.estimation.config.settings"
    _inherit = 'res.config.settings'
    
    _columns = {
        'default_window_days': fields.integer('Window days', default_model='stock.estimation.settings', required=True),
        'default_qos': fields.float('Quality of Service', default_model='stock.estimation.settings', required=True),
        'default_include_bom': fields.boolean('Include BoM', default_model='stock.estimation.settings'),
        'default_sigma_factor': fields.float('Sigma Factor', default_model='stock.estimation.settings', required=True),
    } 

    """
    _defaults = {
        'default_window_days': 30,
        'default_qos' : 0.7,
        'default_include_bom' : True,
        'default_sigma_factor' : 3,
    }  
    """

    def create(self, cr, uid, values, context=None):
        ids = self.search(cr, uid, [])
        if ids and ids[0]:
            id=ids[0]
            self.write(cr, uid, [id], values, context)
        else:
            id = super(stock_estimation_config_settings, self).create(cr, uid, values, context)
        return id

stock_estimation_config_settings()