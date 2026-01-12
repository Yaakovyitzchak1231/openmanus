def reverse_string(s):
    return s[::-1]

# Simple test for the function
if __name__ == '__main__':
    test_string = 'OpenManus'
    reversed_string = reverse_string(test_string)
    print(f'Reversed string of "{test_string}" is "{reversed_string}"')