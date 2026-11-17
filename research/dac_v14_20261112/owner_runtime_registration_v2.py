"""Prospective registration lifecycle fix; not installed in frozen CP1r3."""
import copy
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind_runtime(registration, runtime_config):
    """Bind runtime before sealing, without changing the role/request objects."""
    runtime = Path(runtime_config).resolve(strict=True)
    name = str(runtime)
    fingerprint = digest(runtime)
    result = copy.deepcopy(registration)
    # deepcopy preserves aliases: the preparer shares this dictionary with
    # individual roles. Detach only the top-level table before adding runtime.
    bindings = dict(result['source_sha256'])
    result['source_sha256'] = bindings
    if 'runtime_config' in result:
        assert result['runtime_config'] == name, 'Different runtime path'
        assert bindings.get(name) == fingerprint, 'Runtime bytes changed'
    else:
        assert name not in bindings, 'Partial runtime binding'
        result['runtime_config'] = name
        bindings[name] = fingerprint
    return result


def bind_for_execution(transaction, runtime_config):
    """A sealed owner must already be bound; ordinary unsealed scopes may bind."""
    tx = Path(transaction)
    assert not (tx/'execution_registration.json').exists(), 'Never bind/relaunch an existing attempt'
    path = tx/'registration.json'
    before = path.read_bytes()
    registration = json.loads(before)
    bound = bind_runtime(registration, runtime_config)
    preparation = tx/'preparation.json'
    if preparation.exists():
        seal = json.loads(preparation.read_bytes())
        assert seal['passed'] and seal['transaction_registered']
        assert seal['registration_sha256'] == hashlib.sha256(before).hexdigest(), 'Prepared bytes changed'
        assert registration == bound, 'Owner runtime must be bound before preparation seal'
    elif registration != bound:
        path.write_text(json.dumps(bound, indent=2)+'\n')
    return digest(path)
