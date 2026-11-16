东盟医疗人工智能本地化验证注册库

用途范围：Repository.register_scope 记录人群和用途，link_cohort 将人群证据
关联范围；issue_scope 签发时固定队列版本和指纹，证据在签发前改变须重新关联。
restrict_scope 在已签发记录之上追加后续限制意见，不覆盖既有结论。scope_history
可查范围的签发及限制历史。cohort_guard 提供基础 Wilson 统计和同意范围判断。

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
