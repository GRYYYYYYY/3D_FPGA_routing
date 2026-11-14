#!/usr/bin/env python3
"""Prepare an independent dynamic native transaction+analysis workspace."""
import shutil,subprocess
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
src=D/'analysis_queue_workspace_01';out=D/'native_repair_queue_workspace_01';assert not out.exists();assert shutil.disk_usage(D).free>=80*1024**3
subprocess.run(['cp','-a','--reflink=auto',str(src),str(out)],check=True)
# The current frozen quality batch uses resource_domain_stage_01, untouched.
resource_ws=D/'resource_domain_workspace_01';resource_binding=read(D/'resource_domain_stage_01/binding.json');assert all(sha(resource_ws/n)==h for n,h in resource_binding['source_sha256'].items())
merged=['vpr/src/route/router_stats.h','vpr/src/route/serial_connection_router.cpp','vpr/src/route/h3d_joint_native_repair.h']
for n in merged:shutil.copy2(resource_ws/n,out/n)
header=out/'vpr/src/base/h3d_analysis_queue.h';s=header.read_text().replace('#include <chrono>','#include <chrono>\n#include <cmath>');s=s.replace('std::string route, directory, trailing;', 'std::string route, directory, trailing, operation = "analysis", native_request, objective, crossing_domain;\n        double pressure = 1.;')
old='''            if (!(input >> std::quoted(route) >> std::quoted(directory) >> echo) || (input >> trailing) || (echo != 0 && echo != 1) || !fs::path(route).is_absolute() || !fs::path(directory).is_absolute() || !fs::is_regular_file(route) || !fs::is_directory(directory))
                throw std::runtime_error("Invalid route or private directory");'''
new='''            if (!(input >> std::quoted(route) >> std::quoted(directory) >> echo) || (echo != 0 && echo != 1) || !fs::path(route).is_absolute() || !fs::path(directory).is_absolute() || !fs::is_regular_file(route) || !fs::is_directory(directory))
                throw std::runtime_error("Invalid route or private directory");
            // A missing suffix retains the original analysis request protocol.
            input >> std::ws;
            if (!input.eof()) {
                if (!(input >> std::quoted(operation)) || operation != "repair"
                    || !(input >> std::quoted(native_request) >> std::quoted(objective)
                               >> std::quoted(crossing_domain) >> pressure) || (input >> trailing))
                    throw std::runtime_error("Invalid native repair suffix");
                if (!fs::path(native_request).is_absolute() || !fs::is_regular_file(native_request)
                    || (!crossing_domain.empty() && (!fs::path(crossing_domain).is_absolute()
                                                    || !fs::is_regular_file(crossing_domain)))
                    || (objective != "weighted_soft" && objective != "weighted_capacity"
                        && objective != "physical_soft" && objective != "physical_capacity")
                    || !std::isfinite(pressure) || pressure <= 0. || pressure > 1000.)
                    throw std::runtime_error("Invalid native repair options");
                native_request = fs::canonical(native_request).string();
                if (!crossing_domain.empty()) crossing_domain = fs::canonical(crossing_domain).string();
            }'''
assert old in s;s=s.replace(old,new)
old='''                setup.FileNameOpts.RouteFile = route;'''
new='''                // Per-job hooks are set only after fork. The parent's loaded
                // context and environment cannot inherit this transaction.
                for (const char* name : {"VPR_JOINT_NATIVE_REQUEST", "VPR_JOINT_NATIVE_OUTPUT",
                                         "VPR_JOINT_NATIVE_OBJECTIVE", "VPR_JOINT_NATIVE_REUSE_CROSSINGS",
                                         "VPR_JOINT_NATIVE_VERTICAL_DOMAIN_TRACE", "VPR_CURRENT_STA_NATIVE_PRESSURE_START"}) {
                    if (setenv(name, "", 1)) _exit(125);
                }
                if (operation == "repair") {
                    const std::string pressure_text = std::to_string(pressure);
                    if (setenv("VPR_JOINT_NATIVE_REQUEST", native_request.c_str(), 1)
                        || setenv("VPR_JOINT_NATIVE_OUTPUT", "joint_native.log", 1)
                        || setenv("VPR_JOINT_NATIVE_OBJECTIVE", objective.c_str(), 1)
                        || setenv("VPR_JOINT_NATIVE_REUSE_CROSSINGS", crossing_domain.c_str(), 1)
                        || setenv("VPR_JOINT_NATIVE_VERTICAL_DOMAIN_TRACE", crossing_domain.empty() ? "" : "vertical_domain.log", 1)
                        || setenv("VPR_CURRENT_STA_NATIVE_PRESSURE_START", pressure_text.c_str(), 1)) _exit(125);
                }
                setup.FileNameOpts.RouteFile = route;'''
assert old in s;s=s.replace(old,new);header.write_text(s)
write(D/'native_repair_queue_preparation_01.json',dict(passed=True,workspace=str(out),base='analysis_queue_stage_01',resource_stage='resource_domain_stage_01',resource_files_merged=merged,changed_queue_header=str(header),source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),header,*[out/n for n in merged],D/'analysis_queue_stage_01/binding.json',D/'resource_domain_stage_01/binding.json']},qualification='Independent native transaction worker after per-child FULL/STA. Native logs describe private candidate trees, never final replacement acceptance. Default analysis protocol stays compatible; final candidate still requires independent serialization/capacity audit and native FULL/STA. Original quality cohorts untouched.'))
print(str(out),flush=True)
