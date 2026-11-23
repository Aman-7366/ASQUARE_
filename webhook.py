"""Optional webhook endpoint. Run separately with: uvicorn webhook:app --port 8001"""
import json
from fastapi import FastAPI,Request,HTTPException
from payments import verify_webhook_signature
from database import get_db,query
app=FastAPI(title='A SQUARE payment webhook')

@app.post('/razorpay/webhook')
async def razorpay_webhook(request: Request):
    body=await request.body(); signature=request.headers.get('X-Razorpay-Signature','')
    if not verify_webhook_signature(body,signature): raise HTTPException(400,'Invalid webhook signature')
    event=json.loads(body or b'{}'); payload=event.get('payload',{})
    payment=payload.get('payment',{}).get('entity',{})
    if event.get('event')=='payment.captured' and payment:
        rp_order=payment.get('order_id'); pid=payment.get('id')
        row=query('SELECT * FROM payments WHERE provider_order_id=?',(rp_order,),one=True)
        if row and row['status']!='captured' and payment.get('amount')==row['amount']*100:
            with get_db() as db:
                db.execute("UPDATE payments SET provider_payment_id=?,status='captured',raw_json=? WHERE id=?",(pid,json.dumps(payment),row['id']))
                db.execute("UPDATE orders SET payment_status='Paid',status='Payment Confirmed',updated_at=CURRENT_TIMESTAMP WHERE id=?",(row['order_id'],))
    return {'received':True}
