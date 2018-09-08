import time
import requests
from bs4 import BeautifulSoup
import json



def pageCrawl(targetUrl,D):
    #输入店家URL，将店家评论等信息加入字典D内
    评分对照表={'非常好':5,"很好":4,'好':3,'一般':2,'很差':1}
    cookies = {
        '_lxsdk_cuid': '15ec3fe0f7f2b-093ade485468aa-3f63450e-144000-15ec3fe0f80c8',
        '_lxsdk': '15ec3fe0f7f2b-093ade485468aa-3f63450e-144000-15ec3fe0f80c8',
        '_hc.v': '7f1dcee5-38a2-01a0-59ac-d84b0a85243b.1506526761',
        '__mta': '209574189.1506526783479.1506526783479.1506526783479.1',
        '_lx_utm': 'utm_source^%^3DBaidu^%^26utm_medium^%^3Dorganic',
        'JSESSIONID': '607B52A169DA045288503A63D4749846',
        'aburl': '1',
        'cy': '1',
        'cye': 'shanghai',
        's_ViewType': '10',
        '_lxsdk_s': '15f772e262d-d69-9c1-06b^%^7C^%^7C93',
    }

    headers = {
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'http://www.dianping.com/search/category/1/10/r801',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }
    u1 = targetUrl
    r = requests.get(u1, headers=headers, cookies=cookies)
    html = r.content
    soup = BeautifulSoup(html, 'html.parser')

    # print(soup)
    # 店名：
    shop_name = list(soup.find('h1', attrs={'class': 'shop-name'}).stripped_strings)[0]
    print(shop_name)
    # 分类：
    shop_tag = soup.find('div', attrs={'class': 'breadcrumb'}).find_all('a')[1].get_text().strip()
    print(shop_tag)
    # 评分：
    score_block = soup.find('span', attrs={'id': 'comment_score'})
    score_list = score_block.find_all('span', attrs={'class': 'item'})
    for score in score_list:
        print(score.get_text())

    # 评论：
    # 从第一页寻找总评论数,一页20个，算出最大页数
    url = u1 + 'review_more?pageno='
    r2 = requests.get(url + '1', headers=headers, cookies=cookies)
    html2 = r2.content
    soup2 = BeautifulSoup(html2, 'html.parser')
    # print(soup2)
    N = soup2.find('em', attrs={"class": "col-exp"}).get_text(separator='\n').strip(r'()')
    N = int(N)
    if N % 20 == 0:
        N_page = int(N / 20)
    else:
        N_page = int(N / 20) + 1
    print(N, N_page)
    # 翻页抓取评论、评分
    all_reviews = {}
    for i in range(N_page):

        r2 = requests.get(url + str(i + 1), headers=headers, cookies=cookies)
        html2 = r2.content
        soup2 = BeautifulSoup(html2, 'html.parser')

        review_block_list = soup2.find_all('div', attrs={'class': 'content'})

        for block in review_block_list:
            review = block.find('div', attrs={'class': 'J_brief-cont'}).strings
            review='\n'.join(review).strip()
            attrs = {}
            print(review+'\n\n')
            usr_score_list = block.find_all('span', attrs={'class': 'rst'})
            for i in usr_score_list:
                scores = list(i.stripped_strings)[0]
                scores = scores.split()
                for kv in scores:
                    k = kv[:-1]
                    v = kv[-1]
                    attrs[k] = v
            comprehensive_score=block.find('div',attrs={'class':'user-info'}).find('span')['title']
            comprehensive_score=评分对照表[comprehensive_score]
            attrs['comprehensive_score']=comprehensive_score
            all_reviews[review] = attrs
            D[shop_name] = all_reviews
        time.sleep(0.5)


if __name__ == '__main__':
    D={}
    myURL='http://www.dianping.com/shop/67580386/'
    pageCrawl(myURL,D)
    print(D)

with open('sample.json', mode='w', encoding='utf-8') as json_file:
    json.dump(D, json_file, ensure_ascii=False)
