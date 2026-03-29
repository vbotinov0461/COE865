@echo off
:: Launch all nodes in their own terminals
start cmd /k "python node.py config1.json"
start cmd /k "python node.py config2.json"
start cmd /k "python node.py config3.json"
start cmd /k "python node.py config4.json"
start cmd /k "python node.py config5.json"
start cmd /k "python node.py config6.json"
start cmd /k "python node.py config7.json"