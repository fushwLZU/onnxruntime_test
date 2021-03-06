# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# Configures sources on a target to use a precompiled header. This function takes a target and
# header name as input. The function will generate a .cpp file that includes the header and is used
# to generate the precompiled header; this source file is added to the target's sources.
function(target_precompiled_header target_name header_name)
    if (MSVC AND CMAKE_VS_PLATFORM_TOOLSET)
        # The input precompiled header source (i.e. the '.h' file used for the precompiled header).
        set(pch_header_path ${header_name})
        get_filename_component(header_base_name ${header_name} NAME_WE)

        # Generate the source file that builds the precompiled header. The generated file will have
        # the same base name as the input header name, but has the .cpp extension.
        set(pch_source_path ${CMAKE_CURRENT_BINARY_DIR}/${target_name}_${header_base_name}.cpp)
        set(pch_source_content "// THIS FILE IS GENERATED BY CMAKE\n#include \"${pch_header_path}\"")
        file(WRITE ${pch_source_path} ${pch_source_content})
        set_source_files_properties(${pch_source_path} PROPERTIES COMPILE_FLAGS "/Yc${pch_header_path}")

        # The target's C++ sources use the precompiled header (/Yu). Source-level properties will
        # take precedence over target-level properties, so this will not change the generated source
        # file's property to create the precompiled header (/Yc).
        target_compile_options(${target_name} PRIVATE $<$<COMPILE_LANGUAGE:CXX>:/Yu${header_name}>)

        # Append generated precompiled source to target's sources.
        target_sources(${target_name} PRIVATE ${pch_source_path})

    endif()
endfunction()
