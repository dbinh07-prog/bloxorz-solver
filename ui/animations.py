"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""

from ursina import curve, invoke


def _is_alive(entity):
    """Kiểm tra entity còn tồn tại và đang hoạt động."""
    if entity is None:
        return False
    try:
        return bool(getattr(entity, "enabled", False) and hasattr(entity, "animate"))
    except Exception:
        return False


def fade_in(entity, duration=0.4):
    if not _is_alive(entity):
        return
    try:
        entity.alpha = 0
        entity.animate("alpha", 1, duration=duration, curve=curve.out_quad)
    except Exception:
        pass


def fade_out(entity, duration=0.4):
    if not _is_alive(entity):
        return
    try:
        entity.animate("alpha", 0, duration=duration, curve=curve.in_quad)
    except Exception:
        pass


def slide_from_bottom(entity, end_y, duration=0.35):
    if not _is_alive(entity):
        return
    try:
        entity.y = end_y - 0.15
        entity.animate_y(end_y, duration=duration, curve=curve.out_quad)
    except Exception:
        pass


def pulse(entity):
    if not _is_alive(entity):
        return
    try:
        entity.animate_scale(
            entity.scale * 1.05,
            duration=0.6,
            curve=curve.in_out_sine_boomerang,
            loop=True,
        )
    except Exception:
        pass


def _execute_animation(entity, anim_fn_name, target_val, duration, curve_fn):
    """Helper gọi an toàn animate_* nếu entity vẫn còn tồn tại khi delay kết thúc."""
    if _is_alive(entity):
        anim_method = getattr(entity, anim_fn_name, None)
        if callable(anim_method):
            try:
                anim_method(target_val, duration=duration, curve=curve_fn)
            except Exception:
                pass


def stagger_slide_in(entities, start_delay=0.15, step_delay=0.08, duration=0.3):
    if not entities:
        return

    for index, entity in enumerate(entities):
        if not _is_alive(entity):
            continue

        try:
            end_y = entity.y
            end_scale = entity.scale

            entity.y = end_y - 0.04
            entity.scale = 0

            delay = start_delay + index * step_delay

            invoke(
                _execute_animation,
                entity,
                "animate_y",
                end_y,
                duration,
                curve.out_quad,
                delay=delay,
            )

            invoke(
                _execute_animation,
                entity,
                "animate_scale",
                end_scale,
                duration,
                curve.out_back,
                delay=delay,
            )
        except Exception:
            pass
