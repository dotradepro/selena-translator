from __future__ import annotations

import argostranslate.package


def available_packages() -> list[dict]:
    argostranslate.package.update_package_index()
    installed = {
        (p.from_code, p.to_code) for p in argostranslate.package.get_installed_packages()
    }
    out: list[dict] = []
    for p in argostranslate.package.get_available_packages():
        out.append(
            {
                "from_code": p.from_code,
                "from_name": p.from_name,
                "to_code": p.to_code,
                "to_name": p.to_name,
                "package_version": getattr(p, "package_version", None),
                "installed": (p.from_code, p.to_code) in installed,
            }
        )
    return out


def install_pair(source: str, target: str) -> dict:
    argostranslate.package.update_package_index()
    candidate = next(
        (
            p
            for p in argostranslate.package.get_available_packages()
            if p.from_code == source and p.to_code == target
        ),
        None,
    )
    if candidate is None:
        raise ValueError(f"no package for {source}->{target}")
    path = candidate.download()
    argostranslate.package.install_from_path(path)
    return {
        "from_code": source,
        "to_code": target,
        "installed": True,
    }


def uninstall_pair(source: str, target: str) -> dict:
    for p in argostranslate.package.get_installed_packages():
        if p.from_code == source and p.to_code == target:
            argostranslate.package.uninstall(p)
            return {"from_code": source, "to_code": target, "installed": False}
    raise ValueError(f"not installed: {source}->{target}")
