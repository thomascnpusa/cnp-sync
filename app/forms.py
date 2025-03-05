from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, TextAreaField, SubmitField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired
from wtforms.widgets import PasswordInput

class ReceiveItemForm(FlaskForm):
    product = SelectField('Product', coerce=str)
    quantity = FloatField('Quantity Received', validators=[DataRequired()])
    batch_number = StringField('Batch Number')
    expiry_date = StringField('Expiry Date (YYYY-MM-DD)')

class ReceiveForm(FlaskForm):
    items = FieldList(FormField(ReceiveItemForm), min_entries=1)
    submit = SubmitField('Receive Inventory')

class ProduceForm(FlaskForm):
    product = SelectField('Product', coerce=str)
    quantity = FloatField('Quantity to Produce', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    is_rush = BooleanField('Rush Order')
    submit = SubmitField('Submit Production Order')

class AdjustInventoryForm(FlaskForm):
    product = SelectField('Product', coerce=str)
    quantity = FloatField('Quantity Adjustment', validators=[DataRequired()])
    reason = StringField('Reason', validators=[DataRequired()])
    submit = SubmitField('Adjust Inventory')

class ManualSaleForm(FlaskForm):
    product = SelectField('Product', coerce=str)
    quantity = FloatField('Quantity', validators=[DataRequired()])
    channel = StringField('Channel', validators=[DataRequired()])
    submit = SubmitField('Record Sale')

class BOMItemForm(FlaskForm):
    component_product = SelectField('Component Product', coerce=str)
    quantity = FloatField('Quantity', validators=[DataRequired()])

class BOMForm(FlaskForm):
    items = FieldList(FormField(BOMItemForm), min_entries=1)
    submit = SubmitField('Add BOM Items')

class ProductDetailForm(FlaskForm):
    notes = TextAreaField('Notes')
    instructions = TextAreaField('Instructions')
    unit_cost = FloatField('Unit Cost ($)', validators=[DataRequired()], default=0.0)
    submit = SubmitField('Update Product Details')

class FulfillForm(FlaskForm):
    order_id = StringField('Order ID', validators=[DataRequired()])
    submit = SubmitField('Fulfill Order')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()], widget=PasswordInput())
    submit = SubmitField('Login')