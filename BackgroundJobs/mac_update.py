import asyncio
from datetime import datetime, timedelta
from Base import SQLPool, aiohttpSession
from aiomysql.cursors import DictCursor
from aiohttp.web_response import Response

class mac_update_status:
    running: bool = False
    last_run: datetime = None

async def mac_update():
    
    while True:
        if mac_update_status.last_run is not None:
            now: timedelta = datetime.now() - mac_update_status.last_run

        await asyncio.sleep(3600)

async def do_mac_update():
    async with SQLPool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            cur: DictCursor = cur
            cur.execute("SELECT `value` FROM `variable` WHERE `name` = 'mac_verify'")
            mac_verify = cur.fetchone()["value"]
            cur.execute("SELECT `value` FROM `variable` WHERE `name` = 'mac_verify_changed'")
            mac_verify_changed = cur.fetchone()["value"]
            cur.execute("SELECT `value` FROM `variable` WHERE `name` = 'source_verify'")
            source_verify = cur.fetchone()["value"]
            cur.execute("SELECT `value` FROM `variable` WHERE `name` = 'source_verify_changed'")
            source_verify_changed = cur.fetchone()["value"]
            ip_query = "SELECT `ip`,`switch_id`,`port`,`port_type`  FROM `ip` WHERE `is_updated` = 0"
            cur.execute(ip_query)
            ip = cur.fetchall()
            switch_query = "SELECT `switch_id`, `upper_id`, `upper_port`, `upper_port_type`, `account`, `password`, `vlan`, `machine_type`, `port_description`, `port_type` FROM `switch`"
            cur.execute(switch_query)
            switch = cur.fetchall()
            payload = {
                "mac_verify": mac_verify,
                "mac_verify_changed": mac_verify_changed,
                "source_verify": source_verify,
                "source_verify_changed": source_verify_changed,
                "ip": ip,
                "switch": switch,
            }
            async with aiohttpSession.session.post("switch-updater/update", json=payload) as resp:
                resp: Response = resp
                if resp.status = 200:
                    update_query = "UPDATE `ip` SET `is_updated` = '1' WHERE `updated` = '0'"
                    cur.execute(update_query)
                    cur.execute("UPDATE `variable` SET `value` = '0' WHERE `variable`.`name` = 'mac_verify_changed'")
                    cur.execute("UPDATE `variable` SET `value` = '0' WHERE `variable`.`name` = 'source_verify_changed'")
