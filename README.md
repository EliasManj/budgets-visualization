# Finance Dashboard

Interactive Finance Dashboard project for personal use, developed using Python, Pandas and Bokeh

* Parses .csv and excel files from bank transaction history
* Filter exprenses by month and by custom tags

![Dashboard Video](img/recording.gif)

Define custom budgets in `budgets.yaml`


```
budgets:
budgets:
  - tag: Food
    category: Expense
    amount: 100
  - tag: Gas
    category: Expense
    amount: 100
  - tag: Shopping
    category: Expense
    amount: 100
  - tag: Home
    category: Expense
    amount: 100
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

