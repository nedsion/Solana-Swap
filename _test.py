import pandas as pd
import random

def test():
    csv = pd.read_csv('data.csv')
    df = pd.DataFrame(csv)
    phone_numbers = df['Số Điện Thoại'].tolist()
    phone_numbers = random.choices(phone_numbers, k=2)
    print(phone_numbers)

test()