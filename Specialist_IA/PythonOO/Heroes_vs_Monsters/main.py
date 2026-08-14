from de import De

d6 = De(1,6)
d4 = De(1,4)



print ("Test d6")
print(d6.minimum)
print(d6.maximum)
for i in range(10):
    print(d6.lance())

print ("Test d4")
print(d4.minimum)
print(d4.maximum)
for i in range(10):
    print(d4.lance())