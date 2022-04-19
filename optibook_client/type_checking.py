from datetime import datetime
from .common_types import InstrumentType, OptionKind, Instrument


def validate_instrument(instrument: Instrument) -> None:
    if not instrument.instrument_id or not instrument.tick_size:
        raise Exception("Invalid instrument definition: instrument id or tick_size is not defined.")

    if instrument.tick_size <= 0:
        raise Exception("Invalid instrument definition: tick_size must be positive.")

    # it's okay to not have an instrument type (e.g. MM_GAME_1)
    if not instrument.instrument_type:
        return

    if instrument.instrument_type == InstrumentType.SPOT:
        _is_spot(instrument)
        return

    if instrument.instrument_type == InstrumentType.OPTION:
        _is_option(instrument)
        return

    # throw by default, if changes are made in the future, this function should be adjusted accordingly
    raise Exception("Invalid instrument definition: instrument validation did not pass.")


def _is_spot(instrument: Instrument) -> None:
    if instrument.base_instrument_id:
        raise Exception("Invalid spot definition: a spot should not have a base_instrument_id.")

    if instrument.expiry:
        raise Exception("Invalid spot definition: a spot should not have an expiry.")

    if instrument.option_kind:
        raise Exception("Invalid spot definition: a spot should not have an option_kind.")

    if instrument.strike:
        raise Exception("Invalid spot definition: a spot should not have a strike.")


def _is_option(instrument: Instrument) -> None:
    if not instrument.base_instrument_id:
        raise Exception("Invalid option definition: base_instrument_id is not defined.")

    if not instrument.expiry:
        raise Exception("Invalid option definition: expiry is not defined.")

    if instrument.expiry < datetime.now():
        raise Exception("Invalid option definition: expiry must be in the future.")

    if not instrument.option_kind:
        raise Exception("Invalid option definition: option_kind is not defined.")

    if instrument.option_kind != OptionKind.PUT and instrument.option_kind != OptionKind.CALL:
        raise Exception("Invalid option definition: option_kind must be OptionKind.PUT or OptionKind.CALL.")

    if not instrument.strike:
        raise Exception("Invalid option definition: strike is not defined.")

    if float(instrument.strike) <= 0:
        raise Exception("Invalid instrument definition: strike must be positive.")
