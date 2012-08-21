from testproject.testservice import TestServer
from nimble.test import TestingClient, test, test_fail, expect_result

server = TestingClient(TestServer)
#SECRET = server.server.SECRET

def add_then_divide_script():
    test(server.load)(5)
    expect_result('6')(server.add)(1)
    expect_result('3')(server.divide)(2)

if __name__=='__main__':
    print '#addThenDivideScript:'
    add_then_divide_script()

