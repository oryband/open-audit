# State Comptroller - WORK IN PROGRESS

Opening auditing data from the [Israeli State Comptroller][website].

## TODO

- [x] Dump [yearly 2015 report][66a] to JSON
  - The yearly report contains defects for all ministries and other offices.
  - Defects are grouped into larger topics, where each topic has a defect list and a "to fix" list.
- [ ] Dump the [Prime Minister's notes on the yearly 2015 report][pm notes] in a similar fashion.
  - The PM's notes add additional context to the Comptroller's defects and amendments.
  - It also adds some replies from the bodies under criticism in the Comptroller's report.
- [ ] For each defect and/or topic, find additional material directly related
  - Bodies' reply given in news discussing specific defects).
  - These additional material could provide additional "follow-up" data that is hard to find.
- [ ] Schedule a meeting with the State Comptroller's people, and get their notes on the issue.

## Code

This directory holds the 2015 yearly report,
extracted manually from the [State Comptroller's website][website] and dumped into YAML files.

A CLI Python script can convert these YAML to JSON
and dump them into Elasticsearch for nice data discovery.


[website]: http://www.mevaker.gov.il
[66a]: http://www.mevaker.gov.il/he/Reports/Pages/358.aspx
[pm notes]: http://www.pmo.gov.il/BikoretHamedina/files/hearot_66a.pdf
