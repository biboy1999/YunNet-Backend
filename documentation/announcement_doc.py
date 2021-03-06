from sanic_openapi import api, doc

from documentation.universal_model import Message


class AnnouncementList:
    post_id = doc.String("Post id")
    title = doc.String("Title name")


class AnnouncementPost:
    post_id = doc.String("Post id")
    title = doc.String("Title name")
    content = doc.String("Content, may contain html")


class AnnouncementGetListDoc(api.API):
    summary = "Get announcement list."

    class SuccessResp:
        code = 200
        description = "On success request"

        model = doc.List(AnnouncementList)

    class FailResp:
        code = 500
        description = "On failed request"

        model = Message

    response = [SuccessResp, FailResp]


class AnnouncementGetPostDoc(api.API):
    summary = "Get announcement post by post_id."

    class SuccessResp:
        code = 200
        description = "On success request"

        model = AnnouncementPost

    class FailResp:
        code = 500
        description = "On failed request"

        model = Message

    response = [SuccessResp, FailResp]
