# parser_base.py

from typing import Dict, Set, List, Tuple, Generator
from collections import OrderedDict

from util import is_test, get_logger

log = get_logger(__file__)

GroupDict = Dict[str,str]

class StateError(Exception): pass
class StateTransitionError(StateError): pass

_State = str

class State:
    _valid_states: Set[_State]
    _valid_transitions: Dict[_State,List[_State]]
    _state: _State

    def __init__(
            self,
            initial_state: _State,
            valid_states: Set[_State],
            valid_transitions: Dict[_State,List[_State]],
            ):
        if initial_state not in valid_states:
            raise StateError('initial state must be valid')
        all_states = set([initial_state])
        all_states.update(valid_transitions.keys())
        for rhs in valid_transitions.values():
            all_states.update(rhs)
        if not all_states.issubset(valid_states):
            invalid_states = all_states - valid_states
            raise StateError('invalid states: ' + ', '.join(invalid_states))
        self._state = initial_state
        self._valid_states = valid_states
        self._valid_transitions = valid_transitions

    def is_valid_state(self, state: _State) -> bool:
        return state in self._valid_states
        
    def is_valid_transition(self, l: _State, r: _State) -> bool:
        return all([
                self.is_valid_state(l),
                self.is_valid_state(r),
                r in self._valid_transitions.get(l,[])
                ])

    def transition(self, next_state: _State):
        if not self.is_valid_state(next_state):
            raise StateError(f'next_state is invalid: {next_state}')
        if not self.is_valid_transition(self._state, next_state):
            raise StateTransitionError(
                f'invalid transition: {self._state} -> {next_state}'
            )
        log.debug(f'{self._state} -> {next_state}')
        self._state = next_state

    def __eq__(self, state: object) -> bool:
        if isinstance(state, _State):
            if not self.is_valid_state(state):
                raise StateError(f'Comparison with invalid state: {state}')
            return self._state == state
        raise StateError('State comparison against not _State [str]')

    def __repr__(self) -> str:
        return f'State({self._state})'


class LineRes:
    res: OrderedDict

    def __init__(self, res: OrderedDict):
        self.res = res

    #def __call__(self, line: str) -> Optional[Tuple[str,GroupDict]]:
    def __call__(self, line: str) -> Generator[Tuple[str,GroupDict],None,None]:
        """Iterate through our resolvers until we exhaust them or
           successfully cause a state transition
        """
        for title, r in self.res.items():
            m = r.match(line)
            if m is None:
                continue
            yield (title, m.groupdict())

class LineParserBase:
    lineRes: LineRes

    def __init__(self, lineRes: LineRes):
        self.lineRes = lineRes

    def feed(self, data: str):
        lines: List[str] = data.split("\n")
        if is_test(): lines = lines[0:30]
        lineRes = self.lineRes
        log.debug(f'parsing {len(lines)} lines')
        for i,line in enumerate(lines):
            i = i+1
            res_gen = lineRes(line)
            try: 
                while True:
                    res = res_gen.__next__()
                    if line.strip():
                        log.debug(f'line {i:3} {line}')
                        log.debug(f'line {i:3} {res}')
                    try:
                        title, groupdict = res
                        self.dispatch(title,groupdict)
                        res_gen.throw(StopIteration)
                    except StateTransitionError:
                        continue
                    except StopIteration:
                        break
            except StopIteration:
                log.error(f'No valid resolution for line: {i}')
                raise Exception('Parser Error')
            except:
                log.error(f'Parser error occured at line: {i}')
                raise

    def dispatch(self, title: str, groupdict: GroupDict):
        ...


