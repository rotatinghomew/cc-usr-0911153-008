东盟医疗人工智能本地化验证注册库

用途范围：Repository.register_scope 记录人群和用途，link_cohort 将人群证据
关联范围；issue_scope 签发时固定队列版本和指纹，证据在签发前改变须重新关联。
restrict_scope 在已签发记录之上追加后续限制意见，不覆盖既有结论。scope_history
可查范围的签发及限制历史。cohort_guard 提供基础 Wilson 统计和同意范围判断。

分层可靠性：statistics.stratified_reliability 按 population_group 分别计算可标注
样本量、患病率下的阳性标签数、缺失率和灵敏度置信区间，输出 supported / sparse /
blocked / no_evidence。缺失标签从分子分母中剔除，绝不当作阴性；不会用总体汇总
结果推导所有群体通过。safety.applicability 结合标签可靠性、患病率、样本量、缺失
和同意用途，给出每个群体范围 retained / narrowed / deferred / blocked 及理由。
未声明用途或同意未覆盖用途时不批准。

适用范围签发与复核：
- issue_scope_checked 只按可靠证据覆盖的条件签发，记录 approved_range。
- review_scope / recheck_scope 在补录、标签更正或同意撤回后重算范围。未签发范围
  重新核对；已签发结论保留原依据，只追加限制意见，不覆盖历史。
- recheck_all_scopes 汇总更正后哪些范围实际发生变化、哪些保持不变。
- scope-history 可追出每个范围为何被保留、缩小、暂缓或阻断。

提交材料：run 额外输出 applicability.json 与 strata.csv（每个群体一行），
summary.json 含 applicable range 与分组结论；scope-ranges.csv 逐范围记录结论、
条件和理由。以上均纳入 manifest 计数与校验。

运行验收：
python3 -m clinic_localizer run --fixture fixtures/acceptance.json --database /tmp/clinic_localizer.sqlite3 --output /tmp/clinic_localizer-output

核验：
python3 -m clinic_localizer verify --database /tmp/clinic_localizer.sqlite3 --output /tmp/clinic_localizer-output

分层比较：
python3 -m clinic_localizer strata --database /tmp/clinic_localizer.sqlite3 --purpose validation

范围复核：先用 review-scope 记录结论；条件满足后再 issue-scope 签发；
补录或更正后用 recheck-scopes 重算受影响范围（可用 --cohort 限定）。
python3 -m clinic_localizer review-scope --database DB --scope S --review-id R
python3 -m clinic_localizer issue-scope --database DB --scope S --issue-id I --review-id R
python3 -m clinic_localizer recheck-scopes --database DB --trigger correction --review-prefix P

范围历史：
python3 -m clinic_localizer scope-history --database /tmp/clinic_localizer.sqlite3 --scope <scope_id>

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.cohorts.test_protocol -v
python3 -m unittest tests.governance.test_stratified_applicability -v

构建检查：
python3 -m compileall -q clinic_localizer tests
