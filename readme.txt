东盟医疗人工智能本地化验证注册库

运行验收：
python3 -m clinic_localizer run --fixture fixtures/acceptance.json --database /tmp/clinic_localizer.sqlite3 --output /tmp/clinic_localizer-output

核验：
python3 -m clinic_localizer verify --database /tmp/clinic_localizer.sqlite3 --output /tmp/clinic_localizer-output

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.cohorts.test_protocol -v

构建检查：
python3 -m compileall -q clinic_localizer tests
