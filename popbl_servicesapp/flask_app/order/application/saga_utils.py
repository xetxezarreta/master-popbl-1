"""
Parent class for the sagas state machine
"""
class State:
    def __init__(self, orchestrator):
        print("STATE: " + str(self))
        self.orchestrator = orchestrator
        self.on_enter()
    def on_event(self, event):
        pass

    def on_enter(self):
        pass

    def __eq__(self,other):
        return str(self) == str(other)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__


class SagaManager():

    def __init__(self):
        self.sagas= dict()
    def add(self, index, saga):
        self.sagas[index] = saga
    def start(self,index):
        self.sagas[index].start()
    def get_saga(self,index):
        return self.sagas[index]