#!/usr/bin/python
#
# Execute Terraform runs and transform
# the output into a json format
#
# Usage:
#   ./tf2json.py apply >> tf2json.log
#   ./tf2json.py destroy >> tf2json.log
#
#########################################
import subprocess
import json
import sys
import re


def run_tf(mode):
    cmd = "terraform " + mode + " -auto-approve"
    proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE,
                            stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()

    log = {}
    log["wrapper_version"] = "1.0.0"
    log["mode"] = mode

    # Remove all color codes and ANSI escape characters
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    log["stdout"] = ansi_escape.sub('', stdout)
    log["stderr"] = ansi_escape.sub('', stderr)

    # Replace vertical linestart with nothing
    ansi_escape = re.compile(r'\xe2\x95\xb7')
    log["stderr"] = ansi_escape.sub('', log["stderr"])
    # Replace vertical linened with nothing
    ansi_escape = re.compile(r'\xe2\x95\xb5')
    log["stderr"] = ansi_escape.sub('', log["stderr"])
    # Replace vertical lines with pipes
    ansi_escape = re.compile(r'\xe2\x94\x82')
    log["stderr"] = ansi_escape.sub('|', log["stderr"])
    # Replace empty vertical lines with nothing
    ansi_escape = re.compile(r'\| \n')
    log["stderr"] = ansi_escape.sub('\n', log["stderr"])

    # Split strings by newline
    log["stdout"] = log["stdout"].splitlines()
    log["stderr"] = log["stderr"].splitlines()
    return log


def check_for_empty_line(line):
    return line == ""


def check_for_modes(line):
    return (
                line == "  + create" or
                line == "  ~ update in-place" or
                line == "  - destroy" or
                line == "-/+ destroy and then create replacement"
           )


def check_for_refresh(line):
    # make this as unique as possible to not catch any other matching string
    return (": Refreshing state... [id=" in line)


def check_for_creating(line):
    return line.endswith("Creating...")


def check_for_plan(line):
    return line.startswith("Plan:")


def check_for_resource_headline(line):
    return line.startswith("  #")


def check_for_resource_startline(line):
    return (
                line.startswith("  +") or
                line.startswith("  ~") or
                line.startswith("  -") or
                line.startswith("-/+")
           )


def check_for_resource_paramter(line):
    return line.startswith("      ")


def check_for_resource_end(line):
    return line == "    }"


def check_for_end_headline(line):
    return (line.startswith("| ") and not line.startswith("|   "))


def check_for_end_content(line):
    return line.startswith("|   ")


def get_parameters(line):
    line = line[2:]

    # currently nested stuff does not work
    if line[-1] == "{":
        param_key = line.split(" ")[0]
        return param_key, {}
    elif line[-1] == "[":
        param_key = line.split(" ")[0]
        return param_key, []
    elif line[:2] == "  ":
        # we are nesting
        return get_parameters(line[2:])
    else:
        param_key = line.split(" ")[0]

        # we do not have a list, but a dict
        if len(line.split(" ")) > 1:
            # the value is after the first equal sign
            param_value = line[(line.find("=") + 2):]
            # If value is written like this: "foobar", trim away quotes.
            if " -> " in param_value:
                tmp_param = param_value
                param_value = {}
                param_value["old_value"] = tmp_param.split(" -> ")[0]
                param_value["new_value"] = tmp_param.split(" -> ")[1]
                if param_value["old_value"][0] == "\"":
                    param_value["old_value"] = param_value["old_value"][1:]
                    param_value["old_value"] = param_value["old_value"][:-1]
                if param_value["new_value"][0] == "\"":
                    # Trim away first "
                    param_value["new_value"] = param_value["new_value"][1:]
                    if (param_value["new_value"][-1] != "\"" and
                            "forces replacement" in param_value["new_value"]):
                        # line has a comment which needs to be trimmed away
                        param_value["new_value"] = \
                            param_value["new_value"].split("\" #")[0]
                    else:
                        # Trim away last "
                        param_value["new_value"] = \
                            param_value["new_value"][:-1]
            else:
                if param_value[0] == "\"":
                    param_value = param_value[1:]
                    param_value = param_value[:-1]
            return param_key, param_value
        else:
            # this is a list
            param_value = param_key
            if param_value[0] == "\"":
                param_value = param_value[1:]
                # trim away also colon
                param_value = param_value[:-2]
            return "", param_value


def clean_logs(log):
    clean_log = {}
    tmp_key = ""
    nesting = False
    nest_type = ""

    for line in log:
        if check_for_empty_line(line):
            pass
        elif check_for_modes(line):
            if "actions" not in clean_log:
                clean_log["actions"] = []
            clean_log["actions"].append(line.lstrip().split(" ")[0])
        elif check_for_refresh(line):
            if "refresh" not in clean_log:
                clean_log["refresh"] = []
            clean_log["refresh"].append(line)
        elif check_for_creating(line):
            if "creating" not in clean_log:
                clean_log["creating"] = []
            clean_log["creating"].append(line)
        elif check_for_plan(line):
            if "plan" not in clean_log:
                clean_log["plan"] = {}
            clean_log["plan"]["add"] = int(line.split(" ")[1])
            clean_log["plan"]["change"] = int(line.split(" ")[4])
            clean_log["plan"]["destroy"] = int(line.split(" ")[7])
        elif check_for_resource_headline(line):
            if "resources" not in clean_log:
                clean_log["resources"] = {}
            key = line[4:].split(" ")[0]
            clean_log["resources"][key] = {}
            tmp_key = key
        elif check_for_resource_startline(line):
            clean_log["resources"][tmp_key]['type'] = line.split("\"")[1]
            clean_log["resources"][tmp_key]['name'] = line.split("\"")[3]
            clean_log["resources"][tmp_key]['action'] = line[0:3].lstrip()
            clean_log["resources"][tmp_key]['parameters'] = {}
        elif check_for_resource_paramter(line):
            # trim away leading spaces
            tmp_line = line[6:]

            if tmp_line[2:][-1] == "[":
                nesting = True
                nest_type = "list"
                param_key, param_attributes = get_parameters(tmp_line)
            elif tmp_line[2:][-1] == "{":
                nesting = True
                nest_type = "dict"
                param_key, param_attributes = get_parameters(tmp_line)
            elif tmp_line[2:][-1] == "]" or tmp_line[2:][-1] == "}":
                nesting = False
            else:
                if nesting:
                    if nest_type == "list":
                        _, tmp_attributes = get_parameters(tmp_line)
                        param_attributes.append(tmp_attributes)
                    elif nest_type == "dict":
                        tmp_param, tmp_attributes = get_parameters(tmp_line)
                        param_attributes[tmp_param] = tmp_attributes
                else:
                    param_key, param_attributes = get_parameters(tmp_line)

            # if we are nesting, don't continue to write something to clean_log
            if nesting:
                continue

            clean_log["resources"][tmp_key]['parameters'][param_key] = \
                param_attributes
        elif check_for_resource_end(line):
            pass
        elif check_for_end_headline(line):
            if "end" not in clean_log:
                clean_log["end"] = []
            clean_log["end"].append({"error": line[2:], "error_details": []})
        elif check_for_end_content(line):
            pos = len(clean_log["end"]) - 1
            clean_log["end"][pos]["error_details"].append(line[4:])
    # endfor

    return clean_log


if __name__ == "__main__":
    if len(sys.argv) != 2:
        msg = {"error": "Not enough arguments provided"}
        json.dump(msg, sys.stdout, indent=4)
        exit()

    if sys.argv[1] not in ["apply", "destroy"]:
        msg = {"error": "Wrong argument provided. Use 'apply' or 'destroy'."}
        json.dump(msg, sys.stdout, indent=4)
        exit()

    tf_log = run_tf(sys.argv[1])

    tf_log['stdout_clean'] = clean_logs(tf_log['stdout'])
    tf_log['stderr_clean'] = clean_logs(tf_log['stderr'])
    json.dump(tf_log, sys.stdout, indent=4)
