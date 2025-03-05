from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, FloatField, StringField, SubmitField, FieldList, FormField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional

class ReceiveItemForm(FlaskForm):
    product = SelectField('Product', choices=[], validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    batch_number = StringField('Batch Number', validators=[Optional()])
    expiry_date = StringField('Expiry Date', validators=[Optional()])

class ReceiveForm(FlaskForm):
    items = FieldList(FormField(ReceiveItemForm), min_entries=1)
    submit = SubmitField('Receive Inventory')

class ProduceForm(FlaskForm):
    product = SelectField('Product', choices=[], validators=[DataRequired()])
    quantity = IntegerField('Quantity to Produce', validators=[DataRequired(), NumberRange(min=1)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Submit Production Order')

class BOMItemForm(FlaskForm):
    component_product = SelectField('Component Product', choices=[], validators=[DataRequired()])
    quantity = FloatField('Quantity per Unit', validators=[DataRequired(), NumberRange(min=0.01)])

class BOMForm(FlaskForm):
    items = FieldList(FormField(BOMItemForm), min_entries=1)
    submit = SubmitField('Update BOM')

class AdjustInventoryForm(FlaskForm):
    product = SelectField('Product', choices=[], validators=[DataRequired()])
    quantity = FloatField('Quantity Adjustment', validators=[DataRequired()], description="Positive to add, negative to subtract")
    reason = StringField('Reason', validators=[DataRequired()])
    submit = SubmitField('Adjust Inventory')

class ManualSaleForm(FlaskForm):
    product = SelectField('Product', choices=[], validators=[DataRequired()])
    quantity = IntegerField('Quantity Sold', validators=[DataRequired(), NumberRange(min=1)])
    channel = StringField('Sales Channel', validators=[DataRequired()], default='Manual')
    submit = SubmitField('Record Sale')

class ProductDetailForm(FlaskForm):
    notes = TextAreaField('Notes', validators=[Optional()])
    instructions = TextAreaField('Instructions', validators=[Optional()])
    submit = SubmitField('Save Notes and Instructions')

class FulfillForm(FlaskForm):
    order_id = StringField('Order ID', validators=[DataRequired()])
    submit = SubmitField('Mark as Fulfilled')