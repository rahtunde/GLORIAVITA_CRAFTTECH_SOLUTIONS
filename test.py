# def powerOfTwo(n):
#     if n == 0:
#         return 1
#     else:
#         power = powerOfTwo(n-1)
#         return power * 2
    
# print(4 **2)

# def powerOfTwo(n):
#     i = 0
#     power = 1
#     while i < n:
#         print(">>",n)
#         print(power)
#         power = power * 2
#         i +=1
#         print("power", power)
#     return power
# print(powerOfTwo(5))

# def factorial(n):
#     assert n >= 0 and int(n) == n, "The number must a positive integer only."
#     if n in [0, 1]:
#         return 1
#     else:
#         return n * factorial(n-1)

# print(factorial(1.5))


# def fibonacci(n):
#     assert n >= 0 and int(n) == n, "Fibonacci number cannot be negative or non integer number."
#     if n in [0, 1]:
#         return n
#     return fibonacci(n-1) + fibonacci(n-2)

# print(fibonacci(21))

# Sum of digit of positive integer

# def sumOfDigit(n):
#     assert n >=0 and int(n) == n, "Only positive integer."
#     if n == 0:
#         return 0
    
#     return int(n % 10) + sumOfDigit(int(n / 10))

# print(sumOfDigit(12))


# def power(base, exp):
#     assert exp >= 0 and int(exp) == exp, "The exponent must be positive integer only."
#     if exp == 0:
#         return 1
#     elif exp == 1:
#         return base
#     return base *  power(base, exp -1)

# print(power(2, -1))

# def gcd(a, b):
#     assert int(a) == a and int(b) == b, "The number must be integer only!"
#     if a < 0:
#         a *= -1
#     if b < 0:
#         b *= -1
        
#     if b == 0:
#         return a 
#     return gcd(b, a % b)


def gcd(a, b):
    assert int(a) == a and int(b) == b, "Positive integer only."
    if a < 0:
        a *= -1
    if b < 0:
        b *= -1
    if b == 0:
        return a
    return gcd(b, a % b)
print(gcd(-60, -48))