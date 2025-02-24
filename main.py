import random
import cookiemaker
import time
import json
import urllib.parse
import httpx
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode
from selenium.webdriver.common.by import By


class Musinsa:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
            "Cookie": self.cookie_make(httpx.get("https://www.무신사").headers)
        }
        self.navercookie = self.cookie()
        self.musinsa = []

    def cookie_make(self, headers):
        cookie = []
        headers = str(headers).replace(": '", "").split("'set-cookie'")[1:]
        for i in headers:
            cookie.append(i.split("; ")[0].replace(", '", ""))
        if len(cookie) == 0:
            cookie = ""
        elif len(cookie) != 1:
            cookie = "; ".join(cookie)
        else:
            cookie = cookie[0]
        return cookie

    def urlClean(self, url):
        return url.split("/")[-1]

    def cookie(self):
        return cookiemaker.Cookiemake().naver_cookie()

    def encryptAES(self, data, key):
        data = data.encode('utf-8')
        key = key.encode('utf-8')
        cipher = AES.new(key, AES.MODE_ECB)
        padded_data = pad(data, AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        return b64encode(encrypted).decode()

    def login(self, data):
        self.headers["Cookie"] = f'{self.headers["Cookie"]}; {self.cookie_make(httpx.get("https://www.무신사/app/api/AdCode/start?url=https://www.무신사/auth/login?referer=https%3A%2F%2Fwww.무신사%2Fmypage&referer=https://www.무신사/mypage", headers=self.headers).headers)}'
        htx = httpx.get("https://www.무신사/auth/login?referer=https://www.무신사/mypage", headers=self.headers)
        soup = BeautifulSoup(htx.text, "html.parser")
        cipherKey = soup.find("input", {"name": "cipherKey"})["value"]
        cipherVersion = soup.find("input", {"name": "cipherVersion"})["value"]
        csrfToken = soup.find("input", {"name": "csrfToken"})["value"]
        encryptMemberId	 = urllib.parse.quote(self.encryptAES(data["id"], cipherKey))
        encryptPassword	 = urllib.parse.quote(self.encryptAES(data["pw"], cipherKey))
        login_data = f'cipherKey={cipherKey}&cipherVersion={cipherVersion}&csrfToken={csrfToken}&eventPage=&eventCode=&referer=https%3A%2F%2Fwww.무신사%2Fmypage&inviteKey=&encryptMemberId={encryptMemberId}&encryptPassword={encryptPassword}&isCheckGoogleRecaptcha=false'
        self.headers["Content-Type"] = "application/x-www-form-urlencoded"
        self.headers["Cookie"] = f'{self.headers["Cookie"]}; {self.cookie_make(httpx.post("https://www.무신사/auth/login", headers=self.headers, data=login_data).headers)}'
        htx = httpx.get("https://my.무신사/api/member/v1/login-status", headers=self.headers)
        print(htx.json()["data"]["memberInfo"]["nickName"])
        data["nick"] = htx.json()["data"]["memberInfo"]["nickName"]

    def getOption(self, data):
        option = httpx.get(f"https://goods-detail.무신사/api2/goods/{data}/v2/options?goodsSaleType=SALE", headers=self.headers).json()["data"]["optionItems"]
        option_data = []
        for i in option:
            option_data.append(f'{i["no"]}:{i["managedCode"]}')
        return option_data

    def cart(self, data):
        payload = f"is_order=1&cart_opt={data['option'].split(':')[-1]}%090%09%090%091%09{data['option'].split(':')[0]}%0A&total_qty=1&limited_qty_yn=N&shop_no=1"
        htx = httpx.post(f"https://www.무신사/orders/cart/save/{data['url']}/0", headers=self.headers, data=payload)
        self.headers["Cookie"] = f'{self.headers["Cookie"]}; {self.cookie_make(htx.headers)}'
        self.musinsa=[]
        while True:
            try:
                htx = httpx.get("https://www.무신사/orders/부정사용을 방지하기 위해 링크 삭제order_form", headers=self.headers)
                cart_data = httpx.post("https://order.무신사/api2/부정사용을 방지하기 위해 링크 삭제v1/orders/order-no", headers=self.headers, data="")
                order_data, pay_data= self.cartData(cart_data.json()["data"], BeautifulSoup(htx.text, "html.parser"))
                httpx.post("https://www.무신사/orders/부정사용을 방지하기 위해 링크 삭제order_ready", headers=self.headers, data=order_data)
                self.headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
                self.headers["Content-Type"] = "application/json"
                break
            except Exception as E:
                error = htx.text.split("title = '")[-1].split("'")[0]
                print(f"{error}로 인한 재시도")
                time.sleep(0.3)

        htx = httpx.post("https://order.무신사/api2/부정사용을 방지하기 위해 링크 삭제v1/orders/payment-session", headers=self.headers, data=json.dumps(pay_data))
        return htx.json()["data"]["paymentUrl"]

    def point(self, data):
        if int(data.split("maximumAvailablePoint = ")[-1].split(";")[0]) >= int(data.split("memberTotalPoint = ")[-1].split(";")[0]):
            return int(data.split("memberTotalPoint = ")[-1].split(";")[0])
        else:
            return int(data.split("maximumAvailablePoint = ")[-1].split(";")[0])

    def cartData(self, cart_data, htx):
        address = json.loads(str(htx).split("defaultMemberAddressJson = ")[-1].split(";")[0])
        cartItems = json.loads(str(htx).split("cartItems = ")[-1].split(";")[0])[0]
        point = self.point(str(htx))
        good_info = urllib.parse.quote(htx.find("input", {"name": "good_info"})["value"]).replace(cart_data["orderNo"], '')
        data = urllib.parse.quote(f'''ord_verify_key={cart_data["orderVerifyKey"]}&
ord_key={cart_data["orderKey"]}&
ord_no={cart_data["orderNo"]}&
order_prd_amt={str(htx).split("order_prd_amt = '")[-1].split("';")[0]}&
order_normal_amt={cartItems["normalPrice"]}&
order_sale_amt={cartItems["normalPrice"]-cartItems["salePrice"]}&
order_dlv_fee=0&
order_coupon_amt=0&
order_cart_coupon_no=0&
order_cart_coupon_nm=&
order_cart_coupon_amt=0&
order_prepoint_amt=0&
order_point_amt={point}&
order_cart_dc_amt=0&
order_dc_amt=0&
order_pay_fee=0&
order_pay_amt={int(str(htx).split("order_prd_amt = '")[-1].split("';")[0])-point}&
ordr_nm={address["name"]}&
ordr_email=&
save_order_email=&
ophone1={address["mobile"].split("-")[0]}&
ophone2={address["mobile"].split("-")[1]}&
ophone3={address["mobile"].split("-")[2]}&
omobile1={address["mobile"].split("-")[0]}&
omobile2={address["mobile"].split("-")[1]}&
omobile3={address["mobile"].split("-")[2]}&
rcvr_nm={address["name"]}&
rtitle={address["title"]}&
rphone1={address["mobile"].split("-")[0]}&
rphone2={address["mobile"].split("-")[1]}&
rphone3={address["mobile"].split("-")[2]}&
rmobile1={address["mobile"].split("-")[0]}&
rmobile2={address["mobile"].split("-")[1]}&
rmobile3={address["mobile"].split("-")[2]}&
rzip_cd1={address["zipcode"]}&
rzip_addr1={address["address1"]}&
rzip_addr2={address["address2"]}&
dlv_msg={address["deliveryMessage"]}&
pay_kind=NAVERPAY&
bank_code=&
bank_number=&
bank_inpnm=&
mobile_yn=N&
app_yn=N&
device_kind=&
pay_method=&
plcc_pay_use_yn={htx.find("input", {"name":"plcc_pay_use_yn"})["value"]}&
cart_dc_event_type=&
good_name={cartItems["goodsName"]}&
master_goods_no={cartItems["goodsNo"]}&
master_goods_name={cartItems["goodsName"]}&
master_goods_form_type={cartItems["goodsFormType"]}&
master_goods_opt_kind_cd={cartItems["goodsOptionKindCode"]}&
good_mny={int(str(htx).split("order_prd_amt = '")[-1].split("';")[0])-point}&
buyr_name={address["name"]}&
buyr_mail=&
buyr_tel1={address["mobile"]}&
buyr_tel2={address["mobile"]}&
rcvr_name={address["name"]}&
rcvr_tel1={address["mobile"]}&
rcvr_tel2={address["mobile"]}&
rcvr_mail=&
rcvr_zipx={address["zipcode"]}&
rcvr_add1={address["address1"]}&
rcvr_add2={address["address2"]}&
ordr_idxx={cart_data["orderNo"]}&
good_info=good_info_that&
res_msg=&
comm_tax_mny={int((int(str(htx).split("order_prd_amt = '")[-1].split("';")[0])-point)/1.1)}&
comm_vat_mny={int((int(str(htx).split("order_prd_amt = '")[-1].split("';")[0])-point)-int((int(str(htx).split("order_prd_amt = '")[-1].split("';")[0])-point)/1.1))}&
comm_free_mny=0&
order_gift=&
Ret_URL={htx.find("input", {"name":"Ret_URL"})["value"]}&
ipgm_date={htx.find("input", {"name":"ipgm_date"})["value"]}&
refund_bank=&
refund_account=&
refund_depositor=&
order_cart_nos={htx.find("input", {"name":"order_cart_nos"})["value"]}&
order_coupon_infos=&
org_server=https://www.무신사&
partnership_discount_name=&
pay_server=https://www.무신사&
user_card_code=&
user_card_quota=&
user_virtual_bank_code=&
pg_kind=naverpay&
old_pg_kind=kcp&
discount_promotion_code=&
discount_promotion_card_code=&
pay_merchant_code=&
discount_promotion_amount=0&
auth_token=&
payment_key=&
enc_code=&
shop_pickup_location=&
appsflyer_info[appsflyer_id]=&
appsflyer_info[att]=&
appsflyer_info[os]=&
appsflyer_info[os_version]=&
appsflyer_info[advertising_id]=&
cashReceiptRegistrationType=NONE&
cashReceiptNumberType=&
cashReceiptRegistrationNumber=&
isSaveCashReceipt=N&
mpToken=&
orderNo={cart_data["orderNo"]}&
orderSignature={cart_data["orderSignature"]}&
timestamp={cart_data["timestamp"]}&
cartIdsText={str(htx).split("cartIdsText = '")[-1].split("';")[0]}&
giftNosText=&
easyOrderYn=N&
partnerAdCode=&
orderAmount[normalAmount]={cartItems["normalPrice"]}&
orderAmount[saleAmount]={str(htx).split("order_prd_amt = '")[-1].split("';")[0]}&
orderAmount[payAmount]={int(str(htx).split("order_prd_amt = '")[-1].split("';")[0])-point}&
orderAmount[deliveryAmount]=0&
discount[prePointAmount]=0&
discount[usePointAmount]={point}&
discount[couponAmount]=0&
discount[cartCouponAmount]=0&
discount[cartDiscountAmount]=0&
discount[memberAndAdDiscountAmount]=0&
payment[payKind]=NAVERPAY&
payment[paymentKey]=&
payment[authToken]=&
payment[encCode]=&
payment[bankCode]=&
refundAccount[bank]=&
refundAccount[account]=&
refundAccount[depositor]=&
cashReceipt[registrationType]=NONE&
cashReceipt[numberType]=&
cashReceipt[registrationNumber]=&
recipient[addressId]={address["id"]}&
recipient[title]={address["title"]}&
recipient[name]={address["name"]}&
recipient[mobile]={address["mobile"]}&
recipient[zipcode]={address["zipcode"]}&
recipient[address1]={address["address1"]}&
recipient[address2]={address["address2"]}&
recipient[deliveryMessage]={address["deliveryMessage"]}&
shopPickup[pickupLocation]=&
orderPromotion[promotionCode]=&
orderPromotion[payMerchantCode]=&
appsFlyer[appsFlyerId]=&
appsFlyer[att]=&
appsFlyer[os]=&
appsFlyer[osVersion]=&
appsFlyer[advertisingId]=&''').replace("%20", "+").replace("%3D", "=").replace("%26", "&").replace("%0A", "").replace("/", "%2F").replace("good_info_that", good_info).replace("\n", "")
        pay_data = {
  "orderNo": str(cart_data["orderNo"]),
  "payKind": "NAVERPAY",
  "member": {
    "name": str(htx).split("memberName = '")[-1].split("';")[0],
    "email": str(htx).split("memberEmail = '")[-1].split("';")[0],
    "phone": str(htx).split("memberMobile = '")[-1].split("';")[0].replace("-", "")
  },
  "cashReceipt": {
    "registrationType": "NONE",
    "numberType": "",
    "registrationNumber": ""
  },
  "orderPromotion": {
    "payMerchantCode": "",
    "cardCode": ""
  },
  "payAmount": int(str(htx).split("order_prd_amt = '")[-1].split("';")[0])-point,
  "taxFreeAmount": 0,
  "payNo": None,
  "cardQuota": None,
  "payMethod": None,
  "promotions": [],
  "goods": [
    {
      "goodsNo": int(cartItems["goodsNo"]),
      "goodsOptionNo": int(cartItems["goodsOptionNo"]),
      "extraOptionIds": cartItems["goodsExtraOptions"],
      "goodsName": cartItems["goodsName"],
      "goodsFormType": cartItems["goodsFormType"],
      "goodsOptionKindCode": cartItems["goodsOptionKindCode"],
      "quantity": int(cartItems["quantity"]),
      "payAmount": int(str(htx).split("order_prd_amt = '")[-1].split("';")[0]),
      "taxYn": cartItems["taxYn"],
      "companyId": cartItems["companyId"],
      "companyType": cartItems["companyType"]
    }
  ],
  "deliveryGroups": [],
  "mpToken": ""
}
        return data, pay_data

    def run(self, data):
        data["url"] = self.urlClean(data["url"])
        option = self.getOption(data["url"])
        n = 1
        print("옵션 선택")
        for i in option:
            print(f"{n} - {i.split(':')[-1]}")
            n += 1
        choose_option = input("옵션을 선택해 주세요:")
        data["option"] = option[int(choose_option)-1]
        payments = self.cart(data)
        '''이후 결제 진행'''


data = {
    "id": "",
    "pw": "",
    "url": "",
    "Pay": ""
}


Musinsa().run(data)
