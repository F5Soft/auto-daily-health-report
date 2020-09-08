import time
from html.parser import HTMLParser

import requests


req_headers_login = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8,zh-TW;q=0.7,zh-CN;q=0.6,zh;q=0.5',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/81.0.4044.138 Safari/537.36',
    'Referer': 'https://xmuxg.xmu.edu.cn/xmu/login?app=214'
}

req_headers_login_post = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8,zh-TW;q=0.7,zh-CN;q=0.6,zh;q=0.5',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/81.0.4044.138 Safari/537.36',
    'Referer': 'https://ids.xmu.edu.cn/authserver/login?service=https://xmuxg.xmu.edu.cn/login/cas/xmu'
}

req_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8,zh-TW;q=0.7,zh-CN;q=0.6,zh;q=0.5',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/81.0.4044.138 Safari/537.36',
    'Referer': 'https://xmuxg.xmu.edu.cn/app/214'
}


class OauthParser(HTMLParser):
    def __init__(self, number: str, password: str):
        super().__init__()
        self.req_body = {'username': number, 'password': password}

    def handle_starttag(self, tag: str, attrs: list):
        if tag == 'input':
            attrs = dict(attrs)
            name = attrs.get('name')
            value = attrs.get('value')
            if name in ['lt', 'dllt', 'execution', '_eventId', 'rmShown']:
                self.req_body[name] = value

    def error(self, message):
        pass

    @staticmethod
    def create_req_body(html: str, number: str, password) -> dict:
        parser = OauthParser(number, password)
        parser.feed(html)
        return parser.req_body


def modified_form_data(form_data: list, form_template: list):
    form_data_dict = {}
    for item in form_data:
        value = {}
        name = item['name']
        hide = bool(item['hide'])
        title = item['title']
        if "本人是否承诺所填报的全部内容" in title:
            value['stringValue'] = '是 Yes'
        elif "学生本人是否填写" in title:
            value['stringValue'] = '是'
        elif item['value']['dataType'] == 'STRING':
            value['stringValue'] = item['value']['stringValue']
        elif item['value']['dataType'] == 'ADDRESS_VALUE':
            value['addressValue'] = item['value']['addressValue']
        form_data_dict[name] = {'hide': hide, 'title': title, 'value': value}

    form_data_modified = []
    for item in form_template:
        name = item['name']
        if name in form_data_dict:
            form_data_modified.append({
                'name': name,
                'title': form_data_dict[name]['title'],
                'value': form_data_dict[name]['value'],
                'hide': form_data_dict[name]['hide']
            })
        else:
            form_data_modified.append({
                'name': name,
                'title': item['title'],
                'value': {},
                'hide': 'label' not in name
            })
    return form_data_modified


def checkin(number: str, password: str):
    session = requests.Session()

    # login page
    req_url = "https://ids.xmu.edu.cn/authserver/login?service=https://xmuxg.xmu.edu.cn/login/cas/xmu"
    res = session.get(req_url, headers=req_headers_login)

    # login post
    req_body = OauthParser.create_req_body(res.text, number, password)
    res = session.post(req_url, req_body, headers=req_headers_login_post)
    cookies = res.cookies.get('SAAS_U')

    # get form id
    req_url = "https://xmuxg.xmu.edu.cn/api/app/214/business/now"
    res = session.get(req_url, headers=req_headers)
    business_id = str(res.json()['data'][0]['business']['id'])

    # get form template
    req_url = "https://xmuxg.xmu.edu.cn/api/formEngine/business/%s/formRenderData?playerId=owner" % business_id
    res = session.get(req_url, headers=req_headers)
    form_template = res.json()['data']['components']

    # get owner modification
    req_url = "https://xmuxg.xmu.edu.cn/api/formEngine/business/%s/myFormInstance" % business_id
    res = session.get(req_url, headers=req_headers)
    form = res.json()['data']
    form_id = form['id']
    form_data = form['formData']

    # post change
    req_url = "https://xmuxg.xmu.edu.cn/api/formEngine/formInstance/" + form_id
    req_body = {"formData": modified_form_data(
        form_data, form_template), "playerId": "owner"}
    session.post(req_url, json=req_body, headers=req_headers)


def check(number: str, password: str):
    session = requests.Session()

    # login page
    req_url = "https://ids.xmu.edu.cn/authserver/login?service=https://xmuxg.xmu.edu.cn/login/cas/xmu"
    res = session.get(req_url, headers=req_headers_login)

    # login post
    req_body = OauthParser.create_req_body(res.text, number, password)
    res = session.post(req_url, req_body, headers=req_headers_login_post)
    cookies = res.cookies.get('SAAS_U')

    # get form id
    req_url = "https://xmuxg.xmu.edu.cn/api/app/214/business/now"
    res = session.get(req_url, headers=req_headers)
    business_id = str(res.json()['data'][0]['business']['id'])
    business_time = str(res.json()['data'][0]['business']['name'])

    # get owner modification
    req_url = "https://xmuxg.xmu.edu.cn/api/formEngine/business/%s/myFormInstance" % business_id
    res = session.get(req_url, headers=req_headers)
    form = res.json()['data']
    form_id = form['id']

    req_url = "https://xmuxg.xmu.edu.cn/api/formEngine/formInstances/%s/changeLogs?playerId=owner&businessId=%s" \
              % (business_id, form_id)
    res = session.get(req_url)
    log = res.json()['data']['logs']

    return len(log) > 0 and business_time == time.strftime("%Y-%m-%d", time.localtime())


def get_cookie(number: str, password: str):
    session = requests.Session()

    # login page
    req_url = "https://ids.xmu.edu.cn/authserver/login?service=https://xmuxg.xmu.edu.cn/login/cas/xmu"
    res = session.get(req_url, headers=req_headers_login)

    # login post
    req_body = OauthParser.create_req_body(res.text, number, password)
    res = session.post(req_url, req_body, headers=req_headers_login_post)
    cookies = res.cookies.get('SAAS_U')
    print(cookies)
    return cookies
