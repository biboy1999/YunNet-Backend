from sanic import Blueprint
from sanic_openapi import api, doc

from Base import messages
from Decorators import permission
from Query import User
from Query.bed import Bed
from Query.group import Group
from Query.ip import Ip
from Query.userinfo import Userinfo

bp_bed_change = Blueprint("management-bed-change")


class change_bed_doc(api.API):
    consumes_content_type = "application/json"
    consumes_location = "body"
    consumes_required = True

    class consumes:
        source_bed = doc.String("Source bed")
        # source_username = doc.String("Source user")
        dest_bed = doc.String("Destination bed")
        # dest_username = doc.String("Destination user")

    consumes = doc.JsonBody(vars(consumes))

    class SuccessResp:
        code = 200
        description = "On success register"

        class model:
            message = doc.String("Error message")

        model = dict(vars(model))

    class FailResp:
        code = 401
        description = "On failed register"

        class model:
            message = doc.String("Error message")

        model = dict(vars(model))

    response = [SuccessResp, FailResp]


@change_bed_doc
@bp_bed_change.route("/bed-change", methods=["PUT"])
@permission("api.bed.exchange")
async def exchange_bed(request):
    source_bed = request.json["source_bed"]
    dest_bed = request.json["dest_bed"]
    # for validate uid
    # source_username = request.json["source_username"]
    # dest_username = request.json["dest_username"]

    source_ip = await Ip.get_ip_by_bed(source_bed)
    dest_ip = await Ip.get_ip_by_bed(dest_bed)

    if source_ip is None or dest_ip is None:
        return messages.BAD_REQUEST
    source_uid = source_ip[0]["uid"]
    source_mac = source_ip[0]["mac"]
    dest_uid = dest_ip[0]["uid"]
    dest_mac = dest_ip[0]["mac"]

    await Ip.assign_user(dest_ip[0]["ip"], source_uid)
    await Ip.assign_mac(dest_ip[0]["mac"], source_mac)
    await Ip.assign_user(source_ip[0]["ip"], dest_uid)
    await Ip.assign_mac(source_ip[0]["mac"], dest_mac)

    return messages.OPERATION_SUCCESS


class delete_user_doc(api.API):
    class SuccessResp:
        code = 200
        description = "On success login"

        class model:
            username = doc.String("Username")

        model = dict(vars(model))

    class FailResp:
        code = 400
        description = "On failed login"

        class model:
            message = doc.String("Error message")

        model = dict(vars(model))

    response = [SuccessResp, FailResp]


@delete_user_doc
@bp_bed_change.route("/bed-change/<username>", methods=["DELETE"])
@permission("api.bed.leave")
async def bp_delete(request, username):
    user = await Userinfo.get_userinfo(username)
    if user is None:
        return messages.USER_DOES_NOT_EXIST

    await User.delete_user(username)

    return messages.OPERATION_SUCCESS


class add_user_doc(api.API):
    consumes_content_type = "application/json"
    consumes_location = "body"
    consumes_required = True

    class consumes:
        username = doc.String("Username")
        nick = doc.String("User's name")
        department = doc.String("User's department")
        back_mail = doc.String("User's backup mail")
        note = doc.String("Additional note")
        bed = doc.String("User's bed")
        is_panda = doc.Boolean("Is user panda")

    consumes = doc.JsonBody(vars(consumes))

    class SuccessResp:
        code = 200
        description = "On success login"

        class model:
            username = doc.String("Username")

        model = dict(vars(model))

    class FailResp:
        code = 400
        description = "On failed login"

        class model:
            message = doc.String("Error message")

        model = dict(vars(model))

    response = [SuccessResp, FailResp]


@add_user_doc
@bp_bed_change.route("/bed-change", methods=["POST"])
@permission("api.bed.add")
async def bp_add_user(request):
    username = request.json["username"]
    user = await Userinfo.get_userinfo(username)

    if user is not None:
        return messages.USER_ALREADY_EXISTS

    username = request.json["username"]
    nick = request.json["nick"]
    department = request.json["department"]
    back_mail = request.json["back_mail"]
    note = request.json["note"]
    bed = request.json["bed"]
    is_panda = request.json["is_panda"]

    # add user
    uid = await User.add_user(username, nick, department, back_mail, note)
    # assign ip
    ip = await Ip.get_ip_by_bed(bed)
    if ip is None or len(ip) != 1:
        return messages.BAD_REQUEST
    ip = ip[0]["ip"]
    await Ip.assign_user(ip, uid)
    # add group
    await Group.add_user_group(username, 2)
    await Group.add_user_group(username, 5)
    if is_panda == True:
        await Ip.set_ip_type(ip, 2)
        await Group.add_user_group(username, 7)

    return messages.OPERATION_SUCCESS
