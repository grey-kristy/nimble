from testproject.testservice import TestServer
from nimble.test import TestingClient, test, test_fail, expect_result

def add_then_divide_script():
    with TestingClient(TestServer) as server:
    #SECRET = server.server.SECRET
        test(server.load)(5)
        expect_result('6')(server.add)(1)
        expect_result('3')(server.divide)(2)
        test(server.save_value)()

if __name__=='__main__':
    print '#addThenDivideScript:'
    add_then_divide_script()
