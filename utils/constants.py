INDUSTRIES = {
    "1": {
        "name": '\u6e38\u620f\u5f00\u53d1',
        "weights": {'tech': 0.4, 'design': 0.4, 'marketing': 0.2},
        "pe_min": 15, "pe_max": 25,
        "dbs_risk": {'tech': 7, 'market': 8, 'policy': 5, 'competition': 9, 'finance': 4},
        "dbs_seeds": {
            '\u5e02\u573a\u6ce2\u52a8': ['Steam \u56fd\u533a\u9650\u4ef7\u4ee4\u6536\u7d27', '\u65b0\u4e3b\u673a\u4e16\u4ee3\u5207\u6362\uff0c\u8001\u5e73\u53f0\u73a9\u5bb6\u6d41\u5931'],
            '\u4eba\u624d\u6d41\u52a8': ['\u7c73\u54c8\u6e38\u5f00\u51fa 2x \u85aa\u8d44\u6316\u89d2\u4e3b\u7a0b', '\u6d77\u5916\u5de5\u4f5c\u5ba4\u56de\u6d41\uff0c\u8d44\u6df1\u7f8e\u672f\u88ab\u6316'],
            '\u653f\u7b56\u53d8\u5316': ['\u7248\u53f7\u5ba1\u6279\u51bb\u7ed3\u4f20\u95fb', '\u672a\u6210\u5e74\u4eba\u9632\u6c89\u8ff7\u65b0\u89c4\u5347\u7ea7'],
            '\u6280\u672f\u7a81\u7834': ['AI 3D \u8d44\u4ea7\u751f\u6210\u6210\u672c\u964d 70%', '\u4e91\u6e38\u620f\u57fa\u5efa\u964d\u4ef7'],
            '\u7ade\u4e89\u5bf9\u624b': ['\u9e45\u5382\u65b0\u6e38 DAU \u7834 500 \u4e07', '\u72ec\u7acb\u5de5\u4f5c\u5ba4\u7206\u6b3e\u5438\u8d70 300%'],
            '\u5ba2\u6237\u53cd\u9988': ['TapTap \u8bc4\u5206 4.2 \u8dcc\u5230 3.8', 'Steam \u5dee\u8bc4\u96c6\u4e2d\u7206\u53d1\u6c2a\u91d1\u592a\u91cd'],
            '\u884c\u4e1a\u8d8b\u52bf': ['\u77ed\u89c6\u9891\u5c0f\u6e38\u620f\u6708\u6d41\u6c34\u8fc7\u4ebf', '\u4e8c\u6b21\u5143\u54c1\u7c7b\u7ee7\u7eed\u5438\u91d1'],
            '\u4f9b\u5e94\u94fe': ['Unity \u5f15\u64ce\u6da8\u4ef7 40%', 'GPU \u670d\u52a1\u5668\u65ad\u4f9b'],
            '\u5a92\u4f53\u5173\u6ce8': ['\u4e0a\u70ed\u641c XX \u865a\u5047\u5ba3\u4f20', 'B \u7ad9 UP \u4e3b\u96c6\u4f53\u5dee\u8bc4'],
            '\u878d\u8d44\u73af\u5883': ['\u7f8e\u5143\u57fa\u91d1\u64a4\u79bb\u4e00\u7ea7\u4f30\u503c\u8170\u65a9', '\u817e\u8baf\u7f51\u6613\u6218\u6295\u6536\u7d27'],
            '\u5408\u4f5c\u4f19\u4f34': ['\u53d1\u884c\u5546\u64a4\u8d44\u5df2\u7b7e\u9879\u76ee\u88ab\u780d', 'IP \u6388\u6743\u65b9\u6da8\u4ef7 3 \u500d'],
            '\u6210\u672c\u538b\u529b': ['\u670d\u52a1\u5668\u5e26\u5bbd\u66b4\u6da8\u6708\u6210\u672c\u52a0 15 \u4e07', '\u4e70\u91cf CPA \u6da8 50%'],
        },
    },
    "2": {
        "name": '\u4e92\u8054\u7f51/SaaS',
        "weights": {'tech': 0.5, 'marketing': 0.3, 'design': 0.2},
        "pe_min": 20, "pe_max": 35,
        "dbs_risk": {'tech': 6, 'market': 7, 'policy': 4, 'competition': 8, 'finance': 5},
        "dbs_seeds": {
            '\u5e02\u573a\u6ce2\u52a8': ['\u4e2d\u5c0f\u4f01\u4e1a IT \u9884\u7b97\u780d 30%', '\u5ba2\u6237\u7eed\u7ea6\u7387\u4ece 95% \u8dcc\u5230 78%'],
            '\u4eba\u624d\u6d41\u52a8': ['\u5927\u5382 P7 \u6d8c\u5165\u521b\u4e1a\u671f\u671b 80 \u4e07\u8d77', 'AI \u5de5\u7a0b\u5e08\u8d77\u85aa 100 \u4e07'],
            '\u653f\u7b56\u53d8\u5316': ['\u6570\u636e\u5b89\u5168\u6cd5\u8fdd\u89c4\u4e0a\u9650 5000 \u4e07', '\u7b49\u4fdd 2.0 \u6d4b\u8bc4\u65b0\u89c4'],
            '\u6280\u672f\u7a81\u7834': ['GPT-5 \u8ba9\u5ba2\u6237 SaaS \u96c6\u4f53\u5931\u8840', '\u5f00\u6e90 LLM \u62c9\u4f4e\u8bad\u7ec3\u6210\u672c 90%'],
            '\u7ade\u4e89\u5bf9\u624b': ['\u9489\u9489\u514d\u8d39\u7248\u65b0\u589e 80% \u4f60\u5bb6\u529f\u80fd', '\u98de\u4e66\u88c1\u5b8c AI \u52a0\u6301\u53cd\u6251'],
            '\u5ba2\u6237\u53cd\u9988': ['NPS \u4ece 45 \u8dcc\u5230 28', '\u4f60\u4eec\u66f4\u65b0\u592a\u6162\u4e86'],
            '\u884c\u4e1a\u8d8b\u52bf': ['Agent \u5316\u91cd\u5851 SaaS \u884c\u4e1a', '\u5782\u76f4 SaaS \u4f30\u503c\u91cd\u5851'],
            '\u4f9b\u5e94\u94fe': ['\u4e91\u5382\u5546\u96c6\u4f53\u6da8\u4ef7 20%', 'OpenAI API \u4ef7\u683c\u8170\u65a9\u5012\u903c'],
            '\u5a92\u4f53\u5173\u6ce8': ['\u79d1\u6280\u5a92\u4f53\u66dd\u5149\u6570\u636e\u51fa\u5883\u95ee\u9898', 'V2EX \u4e0a\u88ab\u626c\u6284\u7ade\u54c1'],
            '\u878d\u8d44\u73af\u5883': ['SaaS \u4f30\u503c PS \u4ece 10x \u8dcc\u5230 4x', '\u7f8e\u5143\u57fa\u91d1\u4e0d\u518d\u770b\u4e2d\u56fd SaaS'],
            '\u5408\u4f5c\u4f19\u4f34': ['\u6e20\u9053\u5546\u5206\u6da6\u4ece 20% \u63d0\u5230 35%', '\u96c6\u6210\u5546\u96c6\u4f53\u5931\u8e2a'],
            '\u6210\u672c\u538b\u529b': ['\u83b7\u5ba2 CAC \u4ece 800 \u6da8\u5230 1500', 'AWS \u9000\u6b3e\u6f6e'],
        },
    },
    "3": {
        "name": '\u7535\u529b/\u80fd\u6e90',
        "weights": {'tech': 0.35, 'marketing': 0.35, 'design': 0.3},
        "pe_min": 8, "pe_max": 15,
        "dbs_risk": {'tech': 4, 'market': 5, 'policy': 9, 'competition': 6, 'finance': 3},
        "dbs_seeds": {
            '\u5e02\u573a\u6ce2\u52a8': ['\u5149\u4f0f\u7ec4\u4ef6\u4ef7\u683c\u66b4\u8dcc 30%', '\u5de5\u5546\u4e1a\u7535\u4ef7\u5e02\u573a\u5316\u653e\u5f00'],
            '\u4eba\u624d\u6d41\u52a8': ['\u56fd\u5bb6\u7535\u7f51\u592e\u4f01\u7f16\u5236\u5438\u5f15\u5de5\u7a0b\u5e08', '985 \u7535\u529b\u7cfb\u9996\u9009\u4f53\u5236\u5185'],
            '\u653f\u7b56\u53d8\u5316': ['\u53cc\u78b3\u76ee\u6807\u63d0\u901f\u65b0\u80fd\u6e90\u8865\u8d34\u9000\u5761', '\u7164\u7535\u7075\u6d3b\u6027\u6539\u9020\u5f3a\u5236\u914d\u5957'],
            '\u6280\u672f\u7a81\u7834': ['\u9499\u9491\u77ff\u5149\u4f0f\u6548\u7387\u7834 30%', '\u957f\u65f6\u50a8\u80fd\u6db2\u6d41\u7535\u6c60\u964d\u672c'],
            '\u7ade\u4e89\u5bf9\u624b': ['\u4e94\u5927\u53d1\u7535\u96c6\u56e2\u5927\u4e3e\u5e76\u8d2d', '\u534e\u80fd\u653e\u5927\u65b0\u80fd\u6e90 300 \u4ebf'],
            '\u5ba2\u6237\u53cd\u9988': ['\u7528\u7535\u5927\u6237\u4e0d\u6ee1\u9519\u5cf0\u9650\u7535', '\u5de5\u4e1a\u56ed\u533a\u6295\u8bc9\u7535\u529b\u54c1\u8d28'],
            '\u884c\u4e1a\u8d8b\u52bf': ['\u865a\u62df\u7535\u5382\u805a\u5408 1GW', '\u5168\u56fd\u7edf\u4e00\u7535\u529b\u5e02\u573a\u8bd5\u8fd0\u884c'],
            '\u4f9b\u5e94\u94fe': ['\u9502\u77ff\u4ef7\u683c\u66b4\u8dcc\u50a8\u80fd\u6210\u672c\u964d 40%', '\u5149\u4f0f\u7845\u7247\u4ea7\u80fd\u8fc7\u5269'],
            '\u5a92\u4f53\u5173\u6ce8': ['\u7164\u77ff\u5b89\u5168\u4e8b\u6545\u8206\u8bba\u5012\u67e5 15 \u5e74', '\u6c11\u4f17\u53cd\u5bf9\u9ad8\u538b\u7ebf\u8fdb\u5c0f\u533a'],
            '\u878d\u8d44\u73af\u5883': ['\u7eff\u503a\u5229\u7387 2.5% \u9669\u8d44\u52a0\u5927\u914d\u7f6e', 'ESG \u57fa\u91d1\u914d\u7f6e\u6bd4\u4f8b\u63d0\u5347'],
            '\u5408\u4f5c\u4f19\u4f34': ['\u56fd\u7535\u6295\u8054\u5408\u4f53\u9879\u76ee\u88ab\u62a2', '\u5206\u5e03\u5f0f\u5149\u4f0f\u6e20\u9053\u5546\u8fdd\u7ea6'],
            '\u6210\u672c\u538b\u529b': ['\u78b3\u914d\u989d\u4ef7 100 \u5143\u6bcf\u5428\u6210\u672c\u52a0 10 \u4e07', '\u8001\u65e7\u706b\u7535\u73af\u4fdd\u6539\u9020\u6210\u672c'],
        },
    },
    "4": {
        "name": '\u91d1\u878d/\u79d1\u6280',
        "weights": {'tech': 0.45, 'design': 0.3, 'marketing': 0.25},
        "pe_min": 25, "pe_max": 40,
        "dbs_risk": {'tech': 5, 'market': 6, 'policy': 8, 'competition': 7, 'finance': 6},
        "dbs_seeds": {
            '\u5e02\u573a\u6ce2\u52a8': ['LPR \u964d 0.5% \u4fe1\u8d37\u9700\u6c42\u964d 30%', '\u80a1\u5e02\u8dcc 300 \u70b9\u7834 4000'],
            '\u4eba\u624d\u6d41\u52a8': ['\u5934\u90e8\u6295\u884c 50 \u85aa\u5728\u627e VP', 'Quant \u88ab\u5bf9\u51b2\u57fa\u91d1 300 \u4e07\u5e74\u85aa\u6316\u8d70'],
            '\u653f\u7b56\u53d8\u5316': ['\u91d1\u878d\u76d1\u7ba1 15 \u53f7\u6587\u6536\u7d27\u73b0\u91d1\u8d37', '\u8de8\u5883\u6570\u636e\u6d41\u52a8\u65b0\u89c4'],
            '\u6280\u672f\u7a81\u7834': ['DeFi 2.0 TVL \u7834 500 \u4ebf', '\u592e\u884c\u6570\u5b57\u4eba\u6c11\u5e01\u5168\u9762\u94fa\u5f00'],
            '\u7ade\u4e89\u5bf9\u624b': ['\u8682\u8681\u96c6\u56e2\u5377\u571f\u91cd\u6765', '\u94f6\u884c\u7cfb\u7406\u8d22\u5b50\u516c\u53f8 1000 \u4ebf\u89c4\u6a21'],
            '\u5ba2\u6237\u53cd\u9988': ['APP \u5d29\u6e83 30 \u5206\u949f\u7528\u6237\u96c6\u4f53\u6295\u8bc9', '\u4fe1\u8d37\u901a\u8fc7\u7387\u4e0d\u8db3 60%'],
            '\u884c\u4e1a\u8d8b\u52bf': ['RWA \u8d5b\u9053\u7206\u53d1\u673a\u6784\u7eb7\u7eb7\u5165\u573a', '\u91d1\u878d\u52a0 AI \u6982\u5ff5\u70ed\u5f97\u53d1\u70eb'],
            '\u4f9b\u5e94\u94fe': ['\u963f\u91cc\u4e91\u91d1\u878d\u4e13\u533a\u6da8 10%', '\u5f6d\u535a\u7ec8\u7aef\u6da8 10%'],
            '\u5a92\u4f53\u5173\u6ce8': ['\u8d22\u65b0\u72ec\u5bb6\u63ed\u9732\u4ee3\u5e01\u98ce\u9669', '\u88ab\u592e\u884c\u7ea6\u8c08\u7684\u6d88\u606f\u6cc4\u9732'],
            '\u878d\u8d44\u73af\u5883': ['\u79d1\u521b\u677f\u91d1\u878d\u79d1\u6280\u653e\u5bbd\u51c6\u5165', '\u6e2f\u4ea4\u6240\u91d1\u878d\u79d1\u6280 IPO \u56de\u6696'],
            '\u5408\u4f5c\u4f19\u4f34': ['\u57ce\u5546\u884c\u8054\u5408\u8d37\u91d1\u878d\u79d1\u6280\u88ab\u62d6', '\u94f6\u884c\u5206\u6da6\u653f\u7b56\u6536\u7d27'],
            '\u6210\u672c\u538b\u529b': ['\u5408\u89c4\u5c3d\u804c\u8c03\u67e5\u6210\u672c\u52a0 50 \u4e07\u6bcf\u4eba', '\u53cd\u6d17\u94b1\u7cfb\u7edf\u5347\u7ea7'],
        },
    },
    "5": {
        "name": '\u533b\u7597/\u751f\u7269',
        "weights": {'tech': 0.6, 'design': 0.2, 'marketing': 0.2},
        "pe_min": 15, "pe_max": 30,
        "dbs_risk": {'tech': 8, 'market': 6, 'policy': 9, 'competition': 5, 'finance': 6},
        "dbs_seeds": {
            '\u5e02\u573a\u6ce2\u52a8': ['\u533b\u4fdd\u96c6\u91c7\u538b\u4ef7\u4eff\u5236\u836f\u5229\u6da6\u51cf 60%', '\u521b\u65b0\u836f\u533b\u4fdd\u8c08\u5224\u780d\u4ef7 50%'],
            '\u4eba\u624d\u6d41\u52a8': ['\u533b\u751f\u96c6\u56e2\u5174\u8d77\u4e09\u7532\u4e3b\u6cbb\u51fa\u8d70', 'Biotech \u6d77\u5f52\u56de\u56fd\u6f6e'],
            '\u653f\u7b56\u53d8\u5316': ['DRG DIP \u5168\u56fd\u63a8\u5f00', '\u521b\u65b0\u836f\u9f13\u52b1\u653f\u7b56\u843d\u5730'],
            '\u6280\u672f\u7a81\u7834': ['ADC \u836f\u7269\u4e09\u671f\u6570\u636e\u7206\u8868', '\u57fa\u56e0\u7f16\u8f91\u4e34\u5e8a\u7a81\u7834'],
            '\u7ade\u4e89\u5bf9\u624b': ['\u6052\u745e\u767e\u6d4e\u795e\u5dde\u5165\u5c40\u4f60\u8d5b\u9053', 'MNC \u5728\u4e2d\u56fd\u540c\u6b65\u4e0a\u5e02'],
            '\u5ba2\u6237\u53cd\u9988': ['KOL \u516c\u5f00\u8d28\u7591 III \u671f\u65b9\u6848', '\u60a3\u8005\u7ec4\u7ec7\u6297\u8bae\u5b9a\u4ef7'],
            '\u884c\u4e1a\u8d8b\u52bf': ['AI \u5236\u836f\u6982\u5ff5\u706b\u70ed CRO \u7206\u4ed3', 'GLP-1 \u7c7b\u836f\u7269\u7206\u6b3e'],
            '\u4f9b\u5e94\u94fe': ['GLP-1 \u591a\u80bd\u539f\u6599\u77ed\u7f3a\u4ef7\u683c 3 \u500d', '\u5b9e\u9a8c\u7334\u4ef7\u683c\u66b4\u6da8'],
            '\u5a92\u4f53\u5173\u6ce8': ['\u88ab\u66dd\u5149\u8d85\u9002\u5e94\u75c7\u4f7f\u7528', '\u533b\u7597\u81ea\u5a92\u4f53\u96c6\u4f53\u53d1\u58f0'],
            '\u878d\u8d44\u73af\u5883': ['\u6e2f\u80a1 18A \u7834\u53d1\u6f6e', '\u7f8e\u5143\u57fa\u91d1\u64a4\u51fa\u4e2d\u56fd Biotech'],
            '\u5408\u4f5c\u4f19\u4f34': ['MNC \u780d\u7ba1\u7ebf\u6388\u6743\u8d39\u8c08\u4e0d\u62e2', 'CRO \u6392\u671f\u5230 18 \u4e2a\u6708\u540e'],
            '\u6210\u672c\u538b\u529b': ['\u4e34\u5e8a III \u671f\u5165\u7ec4\u6162 6 \u4e2a\u6708', '\u7814\u53d1\u8d39\u7528\u7206\u8868'],
        },
    },
    "6": {
        "name": '\u96f6\u552e/\u6d88\u8d39',
        "weights": {'marketing': 0.45, 'design': 0.35, 'tech': 0.2},
        "pe_min": 10, "pe_max": 20,
        "dbs_risk": {'tech': 3, 'market': 8, 'policy': 5, 'competition': 9, 'finance': 5},
        "dbs_seeds": {
            '\u5e02\u573a\u6ce2\u52a8': ['Z \u4e16\u4ee3\u6d88\u8d39\u964d\u7ea7 9.9 \u5305\u90ae\u7206\u5355', '\u9ad8\u5ba2\u5355\u54c1\u7c7b\u8170\u65a9'],
            '\u4eba\u624d\u6d41\u52a8': ['\u4e3b\u64ad\u8fd0\u8425\u88ab\u6316\u89d2\u7ade\u4e1a\u7ea0\u7eb7\u591a', '\u65b0\u9510\u54c1\u724c CMO \u96c6\u4f53\u8df3\u69fd'],
            '\u653f\u7b56\u53d8\u5316': ['\u5e73\u53f0\u4e8c\u9009\u4e00\u88ab\u7f5a\u4e3b\u64ad\u5206\u7ea7', '\u5316\u5986\u54c1\u98df\u54c1\u76d1\u7ba1\u65b0\u89c4'],
            '\u6280\u672f\u7a81\u7834': ['AI \u6570\u5b57\u4eba\u4e3b\u64ad\u6210\u672c\u964d 90%', '\u667a\u80fd\u9009\u54c1 AI \u666e\u53ca'],
            '\u7ade\u4e89\u5bf9\u624b': ['\u767d\u724c\u5de5\u5382\u5e97\u4ef7\u683c\u6218\u6bdb\u5229\u780d\u534a', '\u5c71\u59c6\u76d2\u9a6c\u81ea\u6709\u54c1\u724c\u78be\u538b'],
            '\u5ba2\u6237\u53cd\u9988': ['\u5c0f\u7ea2\u4e66 100 \u52a0\u5dee\u8bc4', '\u6296\u97f3\u8bc4\u8bba\u533a\u7ffb\u8f66'],
            '\u884c\u4e1a\u8d8b\u52bf': ['\u5373\u65f6\u96f6\u552e\u7206\u53d1 3 \u516c\u91cc 30 \u5206\u949f', '\u56fd\u8d27\u65b0\u9510\u7ee7\u7eed\u6d17\u724c'],
            '\u4f9b\u5e94\u94fe': ['\u4e1c\u5357\u4e9a\u539f\u6599\u65ad\u4f9b\u5907\u8d27\u53ea\u591f 2 \u5468', '\u5de5\u5382\u4ea4\u671f\u5ef6\u957f'],
            '\u5a92\u4f53\u5173\u6ce8': ['\u4e0a 315 \u665a\u4f1a\u8d54 500 \u4e07', '\u88ab\u804c\u4e1a\u6253\u5047\u76ef\u4e0a'],
            '\u878d\u8d44\u73af\u5883': ['\u65b0\u6d88\u8d39\u6ce1\u6cab\u7834\u706d B \u8f6e\u5012\u6302', '\u7ebf\u4e0b\u6d88\u8d39\u590d\u82cf'],
            '\u5408\u4f5c\u4f19\u4f34': ['\u8fbe\u4eba\u5751\u4f4d\u8d39\u52a0\u9000\u8d27 60% \u53cc\u91cd\u66b4\u51fb', 'MCN \u8dd1\u8def'],
            '\u6210\u672c\u538b\u529b': ['\u6296\u97f3 CPC \u6da8 3 \u500d', '\u5305\u88c5\u6750\u6599\u6da8\u4ef7'],
        },
    },
}

CEO_TRAITS = {
    '1': {"name": '\u6280\u672f\u9886\u8896', "effect": '\u7814\u53d1\u4ea7\u80fd+2\uff0c\u6280\u672f\u7a81\u7834\u6982\u7387+20%'},
    '2': {"name": '\u5546\u4e1a\u5947\u624d', "effect": '\u8c08\u5224\u4f30\u503c\u6ea2\u4ef7+20%\uff0c\u5e02\u573a\u63a8\u5e7f\u6548\u679c+15%'},
    '3': {"name": '\u7ba1\u7406\u94c1\u8155', "effect": '\u5458\u5de5\u5fe0\u8bda\u4e0b\u9650+20\uff0c\u6bcf\u56de\u5408\u514d\u8d39\u7763\u4fc31\u6b21'},
}

ACHIEVEMENTS = {
    'first_dev': ('\U0001f3d7\ufe0f \u9996\u6b21\u7acb\u9879', '\u5b8c\u6210\u7b2c\u4e00\u4e2a\u7814\u53d1\u9879\u76ee'),
    'first_funding': ('\U0001f4b0 \u9996\u6b21\u878d\u8d44', '\u5b8c\u6210\u7b2c\u4e00\u8f6e\u878d\u8d44'),
    'first_hire': ('\U0001f464 \u9996\u4f4d\u5458\u5de5', '\u62db\u52df\u7b2c\u4e00\u540d\u5458\u5de5'),
    'ipo': ('\U0001f389 \u6572\u949f\u4e0a\u5e02', '\u6210\u529f IPO'),
    'office_up': ('\U0001f3d9\ufe0f \u5347\u7ea7\u529e\u516c\u5ba4', '\u6362\u5230 B \u6863\u6216\u66f4\u9ad8'),
    'reputation_100': ('\u2b50 \u4e1a\u754c\u77e5\u540d', '\u58f0\u8a89\u8fbe\u5230 100'),
    'rich': ('\U0001f48e \u767e\u4e07\u73b0\u91d1', '\u73b0\u91d1\u8fbe\u5230 100 \u4e07'),
    'survivor': ('\U0001f6e1\ufe0f \u6491\u8fc7 12 \u6708', '\u5b58\u6d3b\u8d85\u8fc7 1 \u5e74 (12 \u6708)'),
    'team_5': ('\U0001f3e2 5 \u4eba\u56e2\u961f', '\u56e2\u961f\u89c4\u6a21\u8fbe\u5230 5 \u4eba (\u542b CEO)'),
    'veteran': ('\U0001f3c6 \u4e09\u5e74\u8001\u5175', '\u5b58\u6d3b\u8d85\u8fc7 3 \u5e74 (36 \u6708)'),
}

OFFICE_TYPES = {
    'A': {'name': '\u57ce\u4e2d\u6751\u5171\u4eab\u5de5\u4f4d', 'rent': 0.05, 'capacity_bonus': 0, 'reputation_bonus': 0, 'hire_bonus': 0.0, 'tier': 0, 'description': '\u6708\u79df 500 \u5757\uff0c6 \u4eba\u6324 30 \u5e73\uff0c\u7a7a\u8c03\u53ea\u5236\u51b7'},
    'B': {'name': '\u8054\u5408\u529e\u516c\u7a7a\u95f4', 'rent': 0.35, 'capacity_bonus': 1, 'reputation_bonus': 0, 'hire_bonus': 0.05, 'tier': 1, 'description': 'WeWork \u7c7b\uff0c\u542b\u4f1a\u8bae\u5ba4/\u5496\u5561/\u6253\u5370/\u793e\u7fa4\u6d3b\u52a8'},
    'C': {'name': '\u79d1\u6280\u56ed\u5b75\u5316\u5668', 'rent': 0.2, 'capacity_bonus': 1, 'reputation_bonus': 5, 'hire_bonus': 0.1, 'tier': 2, 'description': '30 \u5e73\u72ec\u7acb\u529e\u516c\u5ba4 + \u521b\u4e1a\u5bfc\u5e08 + \u6295\u8d44\u4eba\u5bf9\u63a5 + \u653f\u7b56\u7533\u62a5'},
    'D': {'name': '\u7532\u7ea7\u5199\u5b57\u697c', 'rent': 1.2, 'capacity_bonus': 3, 'reputation_bonus': 10, 'hire_bonus': 0.15, 'tier': 3, 'description': '\u5730\u94c1\u53e3 CBD\uff0c80 \u5e73\u7cbe\u88c5\uff0c\u5546\u52a1\u63a5\u5f85\u6709\u9762\u5b50'},
}

LEVEL_EMOJI = {
    'safe': '\U0001f7e2',
    'yellow': '\U0001f7e1',
    'red': '\U0001f7e0',
    'dead': '\u26ab',
}

# CEO 天赋树: 3 分支 × 3 层，每层 1 个天赋
# 分支对应初始特质: 技术领袖 / 商业奇才 / 管理铁腕
TALENT_TREE = {
    'tech': {  # 技术领袖分支
        'name': '技术领袖',
        'talents': {
            't1_rapid_dev': {
                'name': '敏捷研发',
                'desc': '研发进度 +15%/月，立项成本 -2 万',
                'effect': {'dev_speed_bonus': 0.15, 'dev_cost_reduction': 2},
                'tier': 1,
            },
            't2_tech_breakthrough': {
                'name': '技术突破',
                'desc': '项目完成额外 +30 声誉，触发技术突破事件概率 +30%',
                'effect': {'completion_rep_bonus': 30, 'breakthrough_chance': 0.3},
                'tier': 2,
                'requires': 't1_rapid_dev',
            },
            't3_architect': {
                'name': '系统架构师',
                'desc': '研发产能 +3，所有项目并行上限 +1',
                'effect': {'capacity_bonus': 3, 'parallel_projects': 1},
                'tier': 3,
                'requires': 't2_tech_breakthrough',
            },
        },
    },
    'biz': {  # 商业奇才分支
        'name': '商业奇才',
        'talents': {
            't1_funding_master': {
                'name': '融资大师',
                'desc': '融资估值 +25%，稀释 -5%，冷却 -1 月',
                'effect': {'valuation_bonus': 0.25, 'dilution_reduction': 0.05, 'cooldown_reduction': 1},
                'tier': 1,
            },
            't2_market_insight': {
                'name': '市场洞察',
                'desc': '客户增长率 +10%，营销员工效率 +50%',
                'effect': {'customer_growth_bonus': 0.1, 'marketing_efficiency': 0.5},
                'tier': 2,
                'requires': 't1_funding_master',
            },
            't3_negotiator': {
                'name': '谈判大师',
                'desc': 'IPO 估值 ×1.5，办公室升级费 -50%，合作谈判必胜',
                'effect': {'ipo_valuation_multiplier': 1.5, 'office_upgrade_discount': 0.5},
                'tier': 3,
                'requires': 't2_market_insight',
            },
        },
    },
    'mgmt': {  # 管理铁腕分支
        'name': '管理铁腕',
        'talents': {
            't1_loyal_leader': {
                'name': '人心所向',
                'desc': '员工流失率 -50%，招聘成本 -30%，忠诚度下限 +30',
                'effect': {'retention_bonus': 0.5, 'hire_cost_reduction': 0.3, 'loyalty_floor': 30},
                'tier': 1,
            },
            't2_crisis_manager': {
                'name': '危机公关',
                'desc': '声誉不掉至 0 以下，月度负面事件概率 -40%，自动化解 1 次危机/月',
                'effect': {'rep_floor': 0, 'crisis_reduction': 0.4, 'auto_resolve': 1},
                'tier': 2,
                'requires': 't1_loyal_leader',
            },
            't3_cost_cutter': {
                'name': '成本控制师',
                'desc': '固定成本 -20%，办公室租金 -30%，薪资上涨压力 -50%',
                'effect': {'fixed_cost_reduction': 0.2, 'rent_reduction': 0.3, 'salary_pressure_reduction': 0.5, 'ap_bonus': 0},
                'tier': 3,
                'requires': 't2_crisis_manager',
            },
        },
    },
}

# CEO 升级经验表 (累计 XP)
CEO_LEVEL_XP = {
    1: 0,
    2: 100,
    3: 250,
    4: 450,
    5: 700,
    6: 1000,
    7: 1350,
    8: 1750,
    9: 2200,
    10: 2700,
}
