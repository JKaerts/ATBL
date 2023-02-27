import atbl

p = atbl.ATBLParser()
print(p.parse('''ver 1
row
cel
txt Hello
txt world
cel
row
cel
txt Hello
    world
row'''))
