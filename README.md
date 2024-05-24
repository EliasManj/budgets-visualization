# Finance Dashboard

Interactive Finance Dashboard project for personal use, developed using Python, Pandas and Bokeh

* Parses .csv and excel files from bank transaction history
* Filter exprenses by month and by custom tags

Define custom budgets in `budgets.yaml`


```
budgets:
  Food: 500
  Entertainment: 500
  Gas: 500
  Shopping: 500
  Gym: 500
  Productivity: 500
```


Define custom tag keywords in `keywords.yaml` to match txn description to a tag


```
food:
  - soriana
  - losrojo
  - carniceria
  - oxxo
  - walmart

entertainment:
  - youtube
  - netflix
  - spotify

gas:
  - gaxco
  - gasol
  - bp

productivity:
  - chatgpt
  - github
  - copilot
  - udemy
```

![Dashboard Video](img/recording.gif)

