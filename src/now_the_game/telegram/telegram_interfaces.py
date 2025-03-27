from src import Event


class IChatEvent(Event):
    pass


class IMembershipChanged(Event):
    pass


class IMessageEvent(Event):
    pass


class IPollEvent(Event):
    pass


class IUserEvent(Event):
    pass
