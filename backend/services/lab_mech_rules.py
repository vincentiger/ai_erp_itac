# backend/services/lab_mech_rules.py
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, InvalidOperation
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def to_decimal(v: Any) -> Optional[Decimal]:
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None


def round_half_even(value: Any) -> Optional[int]:
    """
    四捨六入，五成雙
    例如：
    24.5 -> 24
    25.5 -> 26
    """
    d = to_decimal(value)
    if d is None:
        return None
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def round_half_up(value: Any) -> Optional[int]:
    d = to_decimal(value)
    if d is None:
        return None
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def round_hardness_value(value: Any, rounding_mode: Any = None) -> Optional[int]:
    if str(rounding_mode or "").strip() == "四捨五入":
        return round_half_up(value)
    return round_half_even(value)


def in_range(value: Any, spec_min: Any = None, spec_max: Any = None) -> bool:
    v = to_decimal(value)
    if v is None:
        return False

    mn = to_decimal(spec_min)
    mx = to_decimal(spec_max)

    if mn is not None and v < mn:
        return False
    if mx is not None and v > mx:
        return False
    return True


def judge_hardness(values: List[Any], spec_min: Any = None, spec_max: Any = None, rounding_mode: Any = None) -> Dict[str, Any]:
    """
    心部/表面硬度：
    - 先算平均
    - 判定值用五成雙
    - 以 judge_value 判定是否在規格內
    """
    nums = [to_decimal(x) for x in values if x not in (None, "")]
    nums = [x for x in nums if x is not None]

    if not nums:
        return {
            "avg_value": None,
            "judge_value": None,
            "result": None,
            "is_out_of_spec": False,
        }

    avg = sum(nums) / Decimal(len(nums))
    judge_value = round_hardness_value(avg, rounding_mode)
    ok = in_range(judge_value, spec_min, spec_max)

    return {
        "avg_value": float(avg),
        "judge_value": judge_value,
        "result": "PASS" if ok else "FAIL",
        "is_out_of_spec": not ok,
    }


def judge_numeric(value: Any, spec_min: Any = None, spec_max: Any = None) -> Dict[str, Any]:
    """
    一般數值型測試：
    drilling_speed / torque / coating_thickness / drive_torque / carburized_layer
    """
    if to_decimal(value) is None:
        return {
            "result": None,
            "is_out_of_spec": False,
        }
    ok = in_range(value, spec_min, spec_max)
    return {
        "result": "PASS" if ok else "FAIL",
        "is_out_of_spec": not ok,
    }


def judge_ok_ng(status: Any) -> Dict[str, Any]:
    """
    OK/NG 類型測試：
    ductility / drive_performance / hydrogen
    """
    s = (status or "").strip().upper()
    if not s:
        return {
            "result": None,
            "is_out_of_spec": False,
        }
    ok = (s == "OK")
    return {
        "result": "PASS" if ok else "FAIL",
        "is_out_of_spec": not ok,
    }


def judge_decarb(hv1: Any, hv2: Any, hv3: Any) -> Dict[str, Any]:
    """
    脫碳層判定：
    HV2 >= HV1 - 30 且 HV3 <= HV1 + 30
    """
    d1 = to_decimal(hv1)
    d2 = to_decimal(hv2)
    d3 = to_decimal(hv3)

    if d1 is None or d2 is None or d3 is None:
        return {
            "hv2_ok": None,
            "hv3_ok": None,
            "result": None,
        }

    hv2_ok = d2 >= (d1 - Decimal("30"))
    hv3_ok = d3 <= (d1 + Decimal("30"))
    ok = hv2_ok and hv3_ok

    return {
        "hv2_ok": hv2_ok,
        "hv3_ok": hv3_ok,
        "result": "PASS" if ok else "FAIL",
    }


def calc_summary(results: List[str]) -> Dict[str, Any]:
    """
    統計 PASS / FAIL 數量
    """
    pass_count = sum(1 for x in results if x == "PASS")
    fail_count = sum(1 for x in results if x == "FAIL")
    if fail_count > 0:
        final_result = "FAIL"
    elif pass_count > 0:
        final_result = "PASS"
    else:
        final_result = ""

    return {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "result": final_result,
    }


def _parse_dt(v: Any) -> Optional[datetime]:
    if v in (None, ""):
        return None

    if isinstance(v, datetime):
        return v

    s = str(v).strip().replace("T", " ")
    # 兼容前端常見格式：YYYY-MM-DD HH:MM:SS
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass

    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass

    return None


def calc_salt_end(start_at: Any, spec_hours: Any) -> Optional[datetime]:
    """
    鹽霧開始時間 + 標準時數 = 結束時間
    """
    dt = _parse_dt(start_at)
    h = to_decimal(spec_hours)

    if dt is None or h is None:
        return None

    return dt + timedelta(hours=int(h))


def judge_salt_spray(actual_hours: Any, spec_hours: Any) -> Dict[str, Any]:
    """
    鹽霧判定：
    actual_hours > spec_hours => PASS
    """
    a = to_decimal(actual_hours)
    s = to_decimal(spec_hours)

    if a is None or s is None:
        return {
            "result": None,
            "is_out_of_spec": False,
        }

    ok = a > s
    return {
        "result": "PASS" if ok else "FAIL",
        "is_out_of_spec": not ok,
    }
