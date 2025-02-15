# -*- coding: utf-8 -*-
import pytest
from mock import MagicMock, patch, DEFAULT

# A dictionary of additional mock objects generated by other fixtures
mock_objs_dict = dict()


@pytest.fixture()
def mock_objs():
    return mock_objs_dict


@pytest.fixture()
def mock_comp_obj(request):
    # Mock hal.component and returned object
    # - Settable and readable pins
    request.instance.pin_values = pin_values = dict(__default=0xDEADBEEF)

    def get_pin(key):
        if key in pin_values:
            value = pin_values[key]
            print("Returning pin %s value=%s" % (key, value))
        else:
            value = pin_values["__default"]
            print("Returning pin %s DEFAULT value=0x%x" % (key, value))
        return value

    def set_pin(key, value):
        print("Setting pin %s value=%s" % (key, value))
        pin_values[key] = value

    mock_objs_dict["comp_name"] = "test_comp"
    comp_getprefix = MagicMock(side_effect=lambda: mock_objs_dict["comp_name"])

    def set_comp_name(n):
        mock_objs_dict["comp_name"] = n

    comp_setprefix = MagicMock(side_effect=set_comp_name)
    mock_comp_obj = MagicMock(name="mock_hal_comp_obj")
    mock_comp_obj.configure_mock(
        name="mock_hal_comp_obj",
        getprefix=comp_getprefix,
        setprefix=comp_setprefix,
        set_pin=set_pin,
        **{
            "__getitem__.side_effect": get_pin,
            "__setitem__.side_effect": set_pin,
        }
    )

    patcher = patch("hal.component", return_value=mock_comp_obj)
    mock_hal = patcher.start()
    mock_objs_dict["hal_comp"] = mock_hal  # Pass hal.component fixture
    yield mock_comp_obj
    patcher.stop()


@pytest.fixture()
def mock_rospy():
    # Mock rospy attributes
    # - rospy.get_param() with settable parameters
    def set_key(key, value):
        get_param_keys[key] = value

    mock_get_param = MagicMock(name="mock_rospy_get_param")
    get_param_keys = dict()
    mock_get_param.side_effect = get_param_keys.get
    mock_get_param.set_key = set_key

    # - rospy.Rate with mock rospy.Rate()
    mock_Rate_obj = MagicMock(name="mock_rospy_Rate_obj")
    mock_Rate = MagicMock(return_value=mock_Rate_obj)

    # - rospy.is_shutdown() that shuts down after a few loops
    mock_is_shutdown = MagicMock(side_effect=[False] * 3 + [True])

    # - rospy.{Subscriber,Publisher,Service}() methods & returned objects
    mock_Subscriber_obj = MagicMock(name="mock_rospy_Subscriber_obj")
    mock_Subscriber = MagicMock(return_value=mock_Subscriber_obj)
    mock_Publisher_obj = MagicMock(name="mock_rospy_Publisher_obj")
    mock_Publisher = MagicMock(return_value=mock_Publisher_obj)
    mock_Service_obj = MagicMock(name="mock_rospy_Service_obj")
    mock_Service = MagicMock(return_value=mock_Service_obj)

    # The patch.multiple() patcher doesn't pass non-DEFAULT
    # attributes; pass them through mock_objs_dict instead
    mock_objs_dict.update(
        dict(
            rospy_get_param=mock_get_param,
            rospy_is_shutdown=mock_is_shutdown,
            rospy_Rate=mock_Rate,
            rospy_Rate_obj=mock_Rate_obj,
            rospy_Subscriber=mock_Subscriber,
            rospy_Subscriber_obj=mock_Subscriber_obj,
            rospy_Publisher=mock_Publisher,
            rospy_Publisher_obj=mock_Publisher_obj,
            rospy_Service=mock_Service,
            rospy_Service_obj=mock_Service_obj,
        )
    )

    # - rospy.log* that prints to stdout, visible in tests
    def log_side_effect_closure(name):
        def log_side_effect(msg_fmt, *args):
            msg = msg_fmt % args
            print("{}:  {}".format(name, msg))

        return log_side_effect

    mock_loginfo = MagicMock(
        name="rospy_loginfo", side_effect=log_side_effect_closure("loginfo")
    )
    mock_logdebug = MagicMock(
        name="rospy_logdebug", side_effect=log_side_effect_closure("logdebug")
    )
    mock_logfatal = MagicMock(
        name="rospy_logfatal", side_effect=log_side_effect_closure("logfatal")
    )

    # patch ropsy
    rpc = dict(
        init_node=DEFAULT,
        loginfo=mock_loginfo,
        logdebug=mock_logdebug,
        logfatal=mock_logfatal,
        get_param=mock_get_param,
        Rate=mock_Rate,
        Subscriber=mock_Subscriber,
        Publisher=mock_Publisher,
        Service=mock_Service,
        is_shutdown=mock_is_shutdown,
    )
    patcher = patch.multiple("rospy", **rpc)
    mock_rospy = patcher.start()

    yield mock_rospy

    patcher.stop()


@pytest.fixture()
def mock_redis_client_obj(request):
    # Mock redis_store.ConfigClient method and returned object
    # - Settable and readable pins
    request.instance.key_value_map = key_value_map = dict(__default=0)

    def get_key(key):
        value = key_value_map.get(key, key_value_map["__default"])
        print("Returning redis key %s value=%s" % (key, value))
        return value

    def set_key(key, value):
        print("Setting redis key %s value=%s" % (key, value))
        key_value_map[key] = value

    mock_client_obj = MagicMock(name="ConfigClient_obj")
    mock_client_obj.configure_mock(
        name="mock_redis_client_obj",
        set_key=set_key,  # Won't increment mock_calls
        on_update_received=list(),
        **{"get_param.side_effect": get_key, "set_param.side_effect": set_key}
    )

    patcher = patch(
        "redis_store.config.ConfigClient", return_value=mock_client_obj
    )
    redis_store = patcher.start()
    mock_objs_dict["redis_store"] = redis_store
    yield mock_client_obj
    patcher.stop()


@pytest.fixture()
def all_patches(mock_comp_obj, mock_rospy, mock_redis_client_obj):
    return mock_comp_obj, mock_rospy, mock_objs, mock_redis_client_obj
